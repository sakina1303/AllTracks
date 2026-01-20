import React, { useState, useRef } from 'react';
import { View, Button, Image, Text, ScrollView, StyleSheet, ActivityIndicator, Alert, TouchableOpacity, Modal, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import { CameraView, useCameraPermissions } from 'expo-camera';

// Deployed Track C API (base64 JSON)
const BACKEND_URL = 'https://finger-match-backend.onrender.com/track-c/api/match';

const PROCESSING_STEPS = [
    'Uploading images to server...',
    'Preprocessing contactless image...',
    'Enhancing fingerprint patterns...',
    'Extracting biometric features...',
    'Preprocessing contact fingerprint...',
    'Applying CLAHE enhancement...',
    'Comparing feature vectors...',
    'Calculating similarity score...',
    'Generating match result...'
];

function CameraWrapper({ takePhoto, setCameraVisible, cameraFacing, onFlip }) {
    const cameraRef = useRef(null);
    return (
        <View style={styles.cameraView}>
            <CameraView
                style={styles.cameraView}
                ref={cameraRef}
                facing={cameraFacing}
            />
            <View style={styles.cameraTopBar}>
                <TouchableOpacity style={styles.flipButton} onPress={onFlip}>
                    <Text style={styles.flipButtonText}>🔄 Flip</Text>
                </TouchableOpacity>
            </View>
            <View style={styles.cameraButtonContainer}>
                <TouchableOpacity
                    style={styles.cameraButton}
                    onPress={async () => {
                        if (cameraRef.current) {
                            await takePhoto(cameraRef.current);
                        }
                    }}
                >
                    <Text style={styles.cameraButtonText}>Take Photo</Text>
                </TouchableOpacity>
                <TouchableOpacity
                    style={[styles.cameraButton, { backgroundColor: '#FF3B30' }]}
                    onPress={() => setCameraVisible(false)}
                >
                    <Text style={styles.cameraButtonText}>Cancel</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
}

export default function TrackCScreen() {
    // Each image keeps a preview URI + a data URL for backend
    const [contactless, setContactless] = useState(null); // { uri, dataUrl }
    const [contact, setContact] = useState(null);         // { uri, dataUrl }
    const [result, setResult] = useState('');
    const [loading, setLoading] = useState(false);
    const [processingStep, setProcessingStep] = useState('');
    const [cameraVisible, setCameraVisible] = useState(false);
    const [cameraFacing, setCameraFacing] = useState('back');
    const [permission, requestPermission] = useCameraPermissions();

    const takePhoto = async (cameraRef) => {
        if (cameraRef) {
            const photo = await cameraRef.takePictureAsync({ quality: 1, base64: true });
            if (photo && photo.uri) {
                const dataUrl = photo.base64 ? `data:image/jpeg;base64,${photo.base64}` : null;
                setContactless({ uri: photo.uri, dataUrl });
            }
            setCameraVisible(false);
            setResult('');
        }
    };

    const pickImage = async (setImage, type) => {
        let res = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ['images'],
            quality: 1,
            allowsEditing: false,
            base64: true,
        });
        if (res && !res.canceled && res.assets && res.assets[0]) {
            const asset = res.assets[0];
            const dataUrl = asset.base64 ? `data:image/jpeg;base64,${asset.base64}` : null;
            setImage({ uri: asset.uri, dataUrl });
            setResult('');
        }
    };

    const sendToBackend = async () => {
        if (!contactless?.dataUrl || !contact?.dataUrl) {
            Alert.alert('Error', 'Please select both contactless and contact fingerprint images (camera or gallery).');
            return;
        }

        // iOS + Expo Go: ATS blocks cleartext HTTP. Prevent repeated "Network request failed".
        if (Platform.OS === 'ios' && BACKEND_URL.startsWith('http://')) {
            const msg =
                'iOS (Expo Go) blocks HTTP requests.\n\n' +
                `Backend URL: ${BACKEND_URL}\n\n` +
                'Fix:\n' +
                '• Use Android for demo, OR\n' +
                '• Build a dev/standalone app (expo run:ios / EAS build), OR\n' +
                '• Deploy Track C over HTTPS and update BACKEND_URL.';
            setResult(msg);
            Alert.alert('HTTP Blocked on iOS', msg);
            return;
        }

        // check backend health before starting long upload
        const checkServerHealth = async (timeoutMs = 5000) => {
            try {
                const healthUrl = BACKEND_URL.replace(/\/api\/.*$/, '/health');
                const controller = new AbortController();
                const id = setTimeout(() => controller.abort(), timeoutMs);
                const resp = await fetch(healthUrl, { method: 'GET', signal: controller.signal });
                clearTimeout(id);
                return resp.ok;
            } catch (e) {
                console.error('Track C Health Check Failed:', e);
                return false;
            }
        };

        const healthy = await checkServerHealth();
        if (!healthy) {
            Alert.alert(
                'Server Unreachable',
                `Cannot connect to backend at ${BACKEND_URL}\n\nPlease check:\n• Backend is running (Render)\n• Device has internet access`
            );
            return;
        }

        setLoading(true);
        setResult('');
        setProcessingStep(PROCESSING_STEPS[0]);

        for (let i = 1; i < PROCESSING_STEPS.length; i++) {
            await new Promise(resolve => setTimeout(resolve, 600));
            setProcessingStep(PROCESSING_STEPS[i]);
        }

        try {
            // Add timeout to prevent hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contactless_image: contactless.dataUrl,
                    contact_image: contact.dataUrl,
                    threshold: 0.5,
                }),
                signal: controller.signal,
            });

            clearTimeout(timeoutId);
            const data = await response.json();
            if (response.ok) {
                const isMatch = data.decision === "MATCH";
                const resultText = `${data.decision}\n\nSimilarity Score: ${(data.score * 100).toFixed(2)}%\nConfidence Level: ${data.confidence}\nProcessing Time: ${data.processing_time_ms}ms\n${data.mode === 'demo' ? '\n⚠️ Demo Mode (Random Scores)' : ''}`;
                setResult(resultText);
            } else {
                setResult(`Error: ${data.detail || 'Unknown error'}`);
            }
        } catch (e) {
            console.error('Track C Connection Error:', e);
            let errorMsg = `Connection Error: ${e.message}`;
            
            if (e.name === 'AbortError') {
                errorMsg = 'Upload timed out after 30 seconds.\n\nThe backend may be slow or unreachable.';
            } else if (e.message.includes('Network request failed')) {
                errorMsg =
                    `Network Error: Cannot reach backend.\n\n` +
                    `Backend URL: ${BACKEND_URL}\n\n` +
                    `Common fixes:\n` +
                    `• Ensure phone has internet access\n` +
                    `• If Android blocks HTTP, enable cleartext traffic (already set in app.json) and rebuild the app\n` +
                    `• Open ${BACKEND_URL.replace('/api/match', '')} in your browser to verify status\n` +
                    `• Check firewall / cloud security group allows port 8000`;
            }
            
            setResult(errorMsg);
            Alert.alert('Connection Failed', errorMsg);
        } finally {
            setLoading(false);
            setProcessingStep('');
        }
    };

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView contentContainerStyle={styles.scrollView}>
                <View style={styles.header}>
                    <Image source={require('../assets/yellowsense_logo.png')} style={styles.brandLogoSmall} />
                    <Text style={styles.brandTitleSmall}>YellowSense</Text>
                </View>

                <View style={{ height: 16 }} />
                <View style={styles.header}>
                    <Text style={styles.title}>Fingerprint Matcher</Text>
                    <Text style={styles.subtitle}>Contactless-to-Contact Biometric System</Text>
                </View>

                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardIcon}></Text>
                        <Text style={styles.cardTitle}>Contactless Capture</Text>
                    </View>
                    <Text style={styles.cardDescription}>Capture finger image using smartphone camera</Text>
                    <TouchableOpacity
                        style={[styles.button, styles.buttonPrimary]}
                        onPress={() => pickImage(setContactless, 'contactless')}
                        disabled={loading}
                    >
                        <Text style={styles.buttonText}>
                            {contactless ? '✓ Selected' : 'Select from Gallery'}
                        </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={[styles.button, styles.buttonPrimary]}
                        onPress={() => setCameraVisible(true)}
                        disabled={loading}
                    >
                        <Text style={styles.buttonText}>Capture with Camera</Text>
                    </TouchableOpacity>
                    {contactless && (
                        <View style={styles.imageContainer}>
                            <Image source={{ uri: contactless.uri }} style={styles.imagePreview} />
                            <View style={styles.imageBadge}>
                                <Text style={styles.imageBadgeText}>✓ Ready</Text>
                            </View>
                        </View>
                    )}
                </View>

                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardIcon}></Text>
                        <Text style={styles.cardTitle}>Contact-Based Print</Text>
                    </View>
                    <Text style={styles.cardDescription}>Traditional fingerprint scanner image</Text>
                    <TouchableOpacity
                        style={[styles.button, styles.buttonPrimary]}
                        onPress={() => pickImage(setContact, 'contact')}
                        disabled={loading}
                    >
                        <Text style={styles.buttonText}>
                            {contact ? '✓ Selected' : ' Select Image'}
                        </Text>
                    </TouchableOpacity>
                    {contact && (
                        <View style={styles.imageContainer}>
                            <Image source={{ uri: contact.uri }} style={styles.imagePreview} />
                            <View style={styles.imageBadge}>
                                <Text style={styles.imageBadgeText}>✓ Ready</Text>
                            </View>
                        </View>
                    )}
                </View>

                <TouchableOpacity
                    style={[
                        styles.matchButton,
                        (!contactless || !contact || loading) && styles.matchButtonDisabled
                    ]}
                    onPress={sendToBackend}
                    disabled={loading || !contactless || !contact}
                >
                    <Text style={styles.matchButtonText}>
                        {loading ? ' Processing...' : ' Match Fingerprints'}
                    </Text>
                </TouchableOpacity>

                {loading && (
                    <View style={styles.loadingContainer}>
                        <ActivityIndicator size="large" color="#f5c345" />
                        <Text style={styles.processingText}>{processingStep}</Text>
                        <View style={styles.loadingBar}>
                            <View style={styles.loadingBarFill} />
                        </View>
                    </View>
                )}

                <Modal
                    visible={cameraVisible}
                    animationType="slide"
                    transparent={false}
                    onRequestClose={() => setCameraVisible(false)}
                >
                    {!permission?.granted ? (
                        <View style={styles.cameraPermissionContainer}>
                            <Text style={styles.cameraPermissionTitle}>Camera Permission Required</Text>
                            <Text style={styles.cameraPermissionText}>
                                Please allow camera access to capture the contactless fingerprint.
                            </Text>
                            <TouchableOpacity
                                style={[styles.button, styles.buttonPrimary]}
                                onPress={requestPermission}
                            >
                                <Text style={styles.buttonText}>Allow Camera</Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                                style={[styles.button, { backgroundColor: '#FF3B30' }]}
                                onPress={() => setCameraVisible(false)}
                            >
                                <Text style={styles.buttonText}>Cancel</Text>
                            </TouchableOpacity>
                        </View>
                    ) : (
                        <View style={styles.cameraContainer}>
                            <CameraWrapper
                                takePhoto={takePhoto}
                                setCameraVisible={setCameraVisible}
                                cameraFacing={cameraFacing}
                                onFlip={() => setCameraFacing(prev => prev === 'back' ? 'front' : 'back')}
                            />
                        </View>
                    )}
                </Modal>

                {result && !loading && (
                    <View style={[
                        styles.resultCard,
                        result.includes('MATCH') && !result.includes('NO MATCH')
                            ? styles.resultSuccess
                            : styles.resultFailure
                    ]}>
                        <Text style={styles.resultIcon}>
                            {result.includes('MATCH') && !result.includes('NO MATCH') ? '✅' : '❌'}
                        </Text>
                        <Text style={styles.resultTitle}>
                            {result.includes('MATCH') && !result.includes('NO MATCH')
                                ? 'Match Found!'
                                : 'No Match'}
                        </Text>
                        <Text style={styles.resultText}>{result}</Text>
                    </View>
                )}

                <Text style={styles.footer}>UIDAI SITAA Track C • Biometric Demo</Text>
            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    brandLogoSmall: {
        width: 40,
        height: 40,
        resizeMode: 'contain',
        marginBottom: 6,
    },
    brandTitleSmall: {
        fontSize: 14,
        fontWeight: '600',
        color: '#FFA500',
        textAlign: 'center',
    },
    cameraContainer: {
        flex: 1,
        backgroundColor: '#000',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 12,
    },
    cameraPermissionContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 24,
        backgroundColor: '#FFFFFF',
    },
    cameraPermissionTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#000000',
        marginBottom: 8,
        textAlign: 'center',
    },
    cameraPermissionText: {
        fontSize: 14,
        color: '#444444',
        marginBottom: 18,
        textAlign: 'center',
        lineHeight: 20,
    },
    cameraView: {
        width: '100%',
        height: '100%',
        borderRadius: 20,
        overflow: 'hidden',
    },
    cameraTopBar: {
        ...StyleSheet.absoluteFillObject,
        alignItems: 'flex-end',
        paddingTop: 18,
        paddingRight: 16,
    },
    flipButton: {
        backgroundColor: 'rgba(0,0,0,0.6)',
        padding: 12,
        borderRadius: 25,
        minWidth: 80,
        alignItems: 'center',
    },
    flipButtonText: {
        color: '#FFF',
        fontSize: 16,
        fontWeight: '600',
    },
    cameraButtonContainer: {
        ...StyleSheet.absoluteFillObject,
        flexDirection: 'row',
        justifyContent: 'space-around',
        alignItems: 'flex-end',
        paddingBottom: 40,
    },
    cameraButton: {
        backgroundColor: '#f5c345',
        padding: 16,
        borderRadius: 12,
        marginHorizontal: 10,
    },
    cameraButtonText: {
        color: '#fff',
        fontWeight: 'bold',
        fontSize: 16,
    },
    container: {
        flex: 1,
        backgroundColor: '#FFFFFF',
    },
    scrollView: {
        padding: 16,
        paddingTop: 12,
    },
    header: {
        alignItems: 'center',
        marginBottom: 16,
        paddingVertical: 8,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#000000',
        marginBottom: 4,
    },
    subtitle: {
        fontSize: 13,
        color: '#666666',
        textAlign: 'center',
    },
    card: {
        backgroundColor: '#F5F5F5',
        borderRadius: 16,
        padding: 16,
        marginBottom: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 3 },
        shadowOpacity: 0.08,
        shadowRadius: 6,
        elevation: 2,
        borderWidth: 1,
        borderColor: '#EEEEEE',
    },
    cardHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 6,
    },
    cardIcon: {
        fontSize: 22,
        marginRight: 8,
    },
    cardTitle: {
        fontSize: 17,
        fontWeight: 'bold',
        color: '#000000',
    },
    cardDescription: {
        fontSize: 13,
        color: '#666666',
        marginBottom: 12,
    },
    button: {
        paddingVertical: 13,
        borderRadius: 10,
        alignItems: 'center',
        marginBottom: 8,
    },
    buttonPrimary: {
        backgroundColor: '#eab328',
    },
    buttonText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '600',
    },
    imageContainer: {
        marginTop: 12,
        position: 'relative',
    },
    imagePreview: {
        width: '100%',
        height: 200,
        borderRadius: 10,
        backgroundColor: '#E8E8E8',
    },
    imageBadge: {
        position: 'absolute',
        top: 10,
        right: 10,
        backgroundColor: '#34C759',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 20,
    },
    imageBadgeText: {
        color: '#FFFFFF',
        fontSize: 12,
        fontWeight: 'bold',
    },
    matchButton: {
        backgroundColor: '#FF3B30',
        paddingVertical: 18,
        borderRadius: 16,
        alignItems: 'center',
        marginVertical: 20,
        shadowColor: '#FF3B30',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.4,
        shadowRadius: 8,
        elevation: 5,
    },
    matchButtonDisabled: {
        backgroundColor: '#CCCCCC',
        shadowOpacity: 0,
    },
    matchButtonText: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: 'bold',
    },
    loadingContainer: {
        backgroundColor: '#F5F5F5',
        borderRadius: 16,
        padding: 30,
        alignItems: 'center',
        marginVertical: 20,
        borderWidth: 1,
        borderColor: '#EEEEEE',
    },
    processingText: {
        color: '#f5c345',
        fontSize: 15,
        marginTop: 15,
        textAlign: 'center',
        fontWeight: '600',
    },
    loadingBar: {
        width: '100%',
        height: 4,
        backgroundColor: '#EEEEEE',
        borderRadius: 2,
        marginTop: 12,
        overflow: 'hidden',
    },
    loadingBarFill: {
        height: '100%',
        backgroundColor: '#f5c345',
        width: '70%',
    },
    resultCard: {
        borderRadius: 16,
        padding: 20,
        marginVertical: 16,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 3 },
        shadowOpacity: 0.2,
        shadowRadius: 6,
        elevation: 4,
        borderWidth: 2,
    },
    resultSuccess: {
        backgroundColor: '#E8F5E9',
        borderColor: '#4CAF50',
    },
    resultFailure: {
        backgroundColor: '#FFEBEE',
        borderColor: '#F44336',
    },
    resultIcon: {
        fontSize: 44,
        marginBottom: 12,
    },
    resultTitle: {
        fontSize: 22,
        fontWeight: 'bold',
        color: '#000000',
        marginBottom: 15,
    },
    resultText: {
        fontSize: 16,
        lineHeight: 24,
        color: '#000000',
        textAlign: 'center',
    },
    footer: {
        color: '#999999',
        fontSize: 12,
        textAlign: 'center',
        marginTop: 30,
        marginBottom: 20,
    },
});
