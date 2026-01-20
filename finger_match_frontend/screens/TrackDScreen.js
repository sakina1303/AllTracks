import React, { useState, useRef } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator, Alert, TouchableOpacity, Modal, Image, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';
// Gallery-based liveness removed (camera-only)

const BACKEND_URL = 'https://finger-match-backend.onrender.com/track-d/api/liveness_check';

export default function TrackDScreen() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState('');
    const [cameraVisible, setCameraVisible] = useState(false);
    const [capturedFrames, setCapturedFrames] = useState([]);
    const [cameraFacing, setCameraFacing] = useState('front');
    const [permission, requestPermission] = useCameraPermissions();
    const cameraRef = useRef(null);
    const [liveStatus, setLiveStatus] = useState(null); // 'LIVE' | 'SPOOF' | null
    const [attackType, setAttackType] = useState(null); // e.g. 'screen_attack'

    const captureMultipleFrames = async () => {
        if (!permission?.granted) {
            const result = await requestPermission();
            if (!result.granted) {
                Alert.alert('Permission Required', 'Camera permission is needed for liveness detection.');
                return;
            }
        }
        setCameraVisible(true);
        setCapturedFrames([]);
        setResult('');
        setLiveStatus(null);
        setAttackType(null);
    };

    const captureFrame = async () => {
        if (cameraRef.current) {
            try {
                const photo = await cameraRef.current.takePictureAsync({ quality: 0.8 });
                if (photo && photo.uri) {
                    setCapturedFrames(prev => {
                        const next = [...prev, photo.uri];
                        if (next.length >= 3) {
                            processLiveness(next);
                        }
                        return next;
                    });
                }
            } catch (e) {
                Alert.alert('Capture Error', e.message);
            }
        }
    };

    // Gallery-based liveness removed (camera-only)

    const processLiveness = async (frames) => {
        if (frames.length < 2) {
            Alert.alert('Error', 'At least 2 frames are required for liveness detection.');
            return;
        }

        // iOS + Expo Go: ATS blocks cleartext HTTP.
        if (Platform.OS === 'ios' && BACKEND_URL.startsWith('http://')) {
            const msg =
                'iOS (Expo Go) blocks HTTP requests.\n\n' +
                `Backend URL: ${BACKEND_URL}\n\n` +
                'Fix:\n' +
                '• Use Android for demo, OR\n' +
                '• Build a dev/standalone app (expo run:ios / EAS build), OR\n' +
                '• Deploy Track D backend over HTTPS.';
            setResult(msg);
            Alert.alert('HTTP Blocked on iOS', msg);
            return;
        }

        // Check backend health before uploading
        const checkServerHealth = async (timeoutMs = 3000) => {
            try {
                const healthUrl = BACKEND_URL.replace(/\/api\/.*$/, '/health');
                const controller = new AbortController();
                const id = setTimeout(() => controller.abort(), timeoutMs);
                const resp = await fetch(healthUrl, { method: 'GET', signal: controller.signal });
                clearTimeout(id);
                return resp.ok;
            } catch (e) {
                return false;
            }
        };

        const healthy = await checkServerHealth();
        if (!healthy) {
            Alert.alert(
                'Server Unreachable', 
                `Backend not responding at ${BACKEND_URL}.\n\nPlease ensure:\n• Device has internet\n• Backend server is running (Render)`
            );
            return;
        }

        setLoading(true);
        setResult('');
        setLiveStatus(null);
        setAttackType(null);

        try {
            const formData = new FormData();
            frames.forEach((uri, index) => {
                formData.append('frames', {
                    uri: uri,
                    name: `frame_${index}.jpg`,
                    type: 'image/jpeg',
                });
            });

            // Increase timeout for multi-image upload
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json',
                },
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            let data = {};
            try {
                data = await response.json();
            } catch (e) {
                setResult('Error: Invalid response from server');
                return;
            }

            if (response.ok) {
                const isLive = data.is_live;
                const confidence = (data.confidence ?? 0) * 100;
                const motionScore = (data.motion_score ?? 0) * 100;
                const textureScore = (data.texture_score ?? 0) * 100;
                const consistencyScore = (data.consistency_score ?? 0) * 100;
                const processingTime = data.processing_time_ms ?? 0;
                const framesAnalyzed = data.frames_analyzed ?? frames.length;
                
                // Generate specific feedback based on scores
                let tips = '';
                if (!isLive) {
                    tips = '\n\n💡 Correction Needed:';
                    if (textureScore < 40) tips += '\n• Image is too blurry. Tap to focus or hold steady.';
                    else if (motionScore < 5) tips += '\n• Too still. Move finger slightly between captures.';
                    else if (consistencyScore < 50) tips += '\n• Too much movement. Keep finger in frame.';
                    else tips += '\n• Try capturing again with better lighting.';
                }

                const resultText = `${isLive ? '✅ LIVE' : '❌ SPOOF DETECTED'}\n\nConfidence: ${confidence.toFixed(1)}%\n\nChecks:\n• Motion Score: ${motionScore.toFixed(1)}%\n• Texture Quality: ${textureScore.toFixed(1)}%\n• Consistency: ${consistencyScore.toFixed(1)}%${tips}\n\nProcessing Time: ${processingTime.toFixed(0)}ms\n${framesAnalyzed} frames analyzed`;
                setResult(resultText);
                setLiveStatus(isLive ? 'LIVE' : 'SPOOF');
                setAttackType(null);
            } else {
                const detail = data && data.detail ? data.detail : `HTTP ${response.status}`;
                setResult(`Error: ${detail}`);
                Alert.alert('Backend Error', detail);
            }
        } catch (e) {
            console.error('Track D Connection Error:', e);
            let errorMsg = `Connection Error: ${e.message}`;
            
            if (e.name === 'AbortError') {
                errorMsg = 'Request timed out after 30 seconds.\n\nThe backend may be processing slowly or unreachable.';
            } else if (e.message.includes('Network request failed')) {
                errorMsg = `Network Error: Cannot reach backend.\n\nBackend URL: ${BACKEND_URL}\n\nCheck:\n• Device has internet access\n• Backend service (Render) is active`;
            }
            
            setResult(errorMsg);
            Alert.alert('Connection Failed', errorMsg);
        } finally {
            setLoading(false);
            setCapturedFrames([]);
        }
    };

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView contentContainerStyle={styles.scrollView}>
                <View style={styles.header}>
                    <Image source={require('../assets/yellowsense_logo.png')} style={styles.brandLogoSmall} />
                    <Text style={styles.brandTitleSmall}>YellowSense</Text>
                </View>

                <View style={{ height: 12 }} />
                <View style={styles.header}>
                    <Text style={styles.title}>Liveness Detection</Text>
                    <Text style={styles.subtitle}>Anti-Spoof Verification</Text>
                </View>

                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardIcon}></Text>
                        <Text style={styles.cardTitle}>Multi-Frame Capture</Text>
                    </View>
                    <Text style={styles.cardDescription}>
                        Capture 3 frames for motion, texture, and consistency analysis.
                    </Text>

                    <TouchableOpacity
                        style={[styles.button, styles.buttonPrimary]}
                        onPress={captureMultipleFrames}
                        disabled={loading}
                    >
                        <Text style={styles.buttonText}>
                            Capture Frames ({capturedFrames.length}/3)
                        </Text>
                    </TouchableOpacity>

                    {capturedFrames.length > 0 && (
                        <View style={styles.framesPreview}>
                            <Text style={styles.framesText}>
                                ✓ {capturedFrames.length} frame(s) captured - {capturedFrames.length >= 3 ? 'Processing...' : `Need ${3 - capturedFrames.length} more`}
                            </Text>
                        </View>
                    )}
                </View>

                <Modal
                    visible={cameraVisible}
                    animationType="slide"
                    transparent={false}
                    onRequestClose={() => {
                        setCameraVisible(false);
                        setCapturedFrames([]);
                        setLiveStatus(null);
                        setAttackType(null);
                    }}
                >
                    {permission?.granted && (
                        <View style={styles.cameraContainer}>
                            <CameraView
                                style={styles.cameraView}
                                ref={cameraRef}
                                facing={cameraFacing}
                            />
                            <View style={styles.cameraOverlay}>
                                <View style={styles.cameraTopBar}>
                                    <TouchableOpacity
                                        style={styles.flipButton}
                                        onPress={() => setCameraFacing(prev => prev === 'front' ? 'back' : 'front')}
                                    >
                                        <Text style={styles.flipButtonText}>🔄 Flip</Text>
                                    </TouchableOpacity>
                                </View>
                                <View style={styles.cameraStatusContainer}>
                                    <Text style={styles.cameraInstruction}>
                                        Frame {capturedFrames.length + 1}/3
                                        {'\n'}Move slightly between captures
                                        {'\n'}Camera: {cameraFacing === 'front' ? 'Front 🤳' : 'Back 📷'}
                                    </Text>
                                    <View style={styles.cameraLivenessBadge}>
                                        {loading && (
                                            <Text style={styles.cameraLivenessText}>
                                                Analyzing for spoof...
                                            </Text>
                                        )}
                                        {!loading && liveStatus && (
                                            <Text
                                                style={[
                                                    styles.cameraLivenessText,
                                                    liveStatus === 'LIVE'
                                                        ? styles.cameraLivenessLive
                                                        : styles.cameraLivenessSpoof
                                                ]}
                                            >
                                                {liveStatus === 'LIVE'
                                                    ? 'Spoof not detected (Real finger)'
                                                    : attackType === 'screen_attack'
                                                        ? 'Spoof detected (Phone / screen)'
                                                        : 'Spoof detected'}
                                            </Text>
                                        )}
                                        {!loading && !liveStatus && (
                                            <Text style={styles.cameraLivenessText}>
                                                Hold your finger steady in front of camera
                                            </Text>
                                        )}
                                    </View>
                                </View>
                                <View style={styles.cameraButtonContainer}>
                                    {!liveStatus && (
                                        <TouchableOpacity
                                            style={styles.cameraButton}
                                            onPress={captureFrame}
                                            disabled={loading}
                                        >
                                            <Text style={styles.cameraButtonText}>
                                                {loading ? '...' : 'Capture'}
                                            </Text>
                                        </TouchableOpacity>
                                    )}
                                    {!!liveStatus && !loading && (
                                        <TouchableOpacity
                                            style={[styles.cameraButton, { backgroundColor: '#34C759' }]}
                                            onPress={() => {
                                                setCameraVisible(false);
                                                setCapturedFrames([]);
                                                setLiveStatus(null);
                                                setAttackType(null);
                                                setResult('');
                                            }}
                                        >
                                            <Text style={styles.cameraButtonText}>Done</Text>
                                        </TouchableOpacity>
                                    )}
                                    <TouchableOpacity
                                        style={[styles.cameraButton, { backgroundColor: '#FF3B30' }]}
                                        onPress={() => {
                                            setCameraVisible(false);
                                            setCapturedFrames([]);
                                            setLiveStatus(null);
                                            setAttackType(null);
                                        }}
                                    >
                                        <Text style={styles.cameraButtonText}>Cancel</Text>
                                    </TouchableOpacity>
                                </View>
                            </View>
                        </View>
                    )}
                </Modal>

                {loading && (
                    <View style={styles.loadingContainer}>
                        <ActivityIndicator size="large" color="#f5c345" />
                        <Text style={styles.processingText}>
                            Analyzing frames for liveness...
                            {'\n'}Checking motion, texture, and consistency
                        </Text>
                    </View>
                )}

                {result && !loading && (
                    <View style={[
                        styles.resultCard,
                        result.includes('LIVE') && !result.includes('SPOOF') 
                            ? styles.resultSuccess 
                            : styles.resultFailure
                    ]}>
                        <Text style={styles.resultIcon}>
                            {result.includes('LIVE') && !result.includes('SPOOF') ? '✅' : '⚠️'}
                        </Text>
                        <Text style={styles.resultTitle}>
                            {result.includes('LIVE') && !result.includes('SPOOF')
                                ? 'Live Person Detected'
                                : 'Spoof Detected'}
                        </Text>
                        <Text style={styles.resultText}>{result}</Text>
                    </View>
                )}

                <Text style={styles.footer}>UIDAI SITAA Track D • Liveness Detection</Text>
            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
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
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#000000',
        marginBottom: 4,
        textAlign: 'center',
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
        marginBottom: 16,
        lineHeight: 19,
    },
    button: {
        paddingVertical: 14,
        borderRadius: 10,
        alignItems: 'center',
        marginBottom: 8,
    },
    buttonPrimary: {
        backgroundColor: '#eab328',
    },
    buttonSecondary: {
        backgroundColor: '#007AFF',
    },
    buttonDisabled: {
        backgroundColor: '#CCCCCC',
    },
    buttonText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '600',
    },
    framesPreview: {
        marginTop: 12,
        padding: 10,
        backgroundColor: '#E8F5E9',
        borderRadius: 8,
    },
    framesText: {
        color: '#2E7D32',
        fontSize: 13,
        fontWeight: '600',
        textAlign: 'center',
    },
    cameraContainer: {
        flex: 1,
    },
    cameraView: {
        flex: 1,
    },
    cameraOverlay: {
        ...StyleSheet.absoluteFillObject,
        justifyContent: 'space-between',
        padding: 20,
    },
    cameraTopBar: {
        alignItems: 'flex-end',
        paddingTop: 10,
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
    cameraInstruction: {
        color: '#FFF',
        fontSize: 18,
        fontWeight: 'bold',
        textAlign: 'center',
        marginTop: 40,
        backgroundColor: 'rgba(0,0,0,0.5)',
        padding: 15,
        borderRadius: 10,
    },
    cameraButtonContainer: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        marginBottom: 40,
    },
    cameraButton: {
        backgroundColor: '#f5c345',
        padding: 16,
        borderRadius: 12,
        minWidth: 120,
        alignItems: 'center',
    },
    cameraButtonText: {
        color: '#fff',
        fontWeight: 'bold',
        fontSize: 16,
    },
    cameraStatusContainer: {
        alignItems: 'center',
        marginTop: 20,
    },
    cameraLivenessBadge: {
        marginTop: 12,
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 20,
        backgroundColor: 'rgba(0,0,0,0.6)',
    },
    cameraLivenessText: {
        color: '#FFF',
        fontSize: 14,
        textAlign: 'center',
        fontWeight: '600',
    },
    cameraLivenessLive: {
        color: '#00E676',
    },
    cameraLivenessSpoof: {
        color: '#FF5252',
    },
    loadingContainer: {
        backgroundColor: '#F5F5F5',
        borderRadius: 14,
        padding: 24,
        alignItems: 'center',
        marginVertical: 16,
        borderWidth: 1,
        borderColor: '#EEEEEE',
    },
    processingText: {
        color: '#f5c345',
        fontSize: 14,
        marginTop: 12,
        textAlign: 'center',
        fontWeight: '600',
        lineHeight: 20,
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
        backgroundColor: '#FFF3E0',
        borderColor: '#FF9800',
    },
    resultIcon: {
        fontSize: 44,
        marginBottom: 12,
    },
    resultTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#000000',
        marginBottom: 12,
        textAlign: 'center',
    },
    resultText: {
        fontSize: 14,
        lineHeight: 22,
        color: '#000000',
        textAlign: 'center',
    },
    footer: {
        color: '#999999',
        fontSize: 11,
        textAlign: 'center',
        marginTop: 20,
        marginBottom: 16,
    },
});
