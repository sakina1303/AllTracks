import React, { useState, useRef } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator, Alert, TouchableOpacity, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';

const BACKEND_URL = 'https://finger-match-backend.onrender.com/track-d/api/liveness_check';

export default function TrackBScreen() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState('');
    const [cameraVisible, setCameraVisible] = useState(false);
    const [capturedFrames, setCapturedFrames] = useState([]);
    const [permission, requestPermission] = useCameraPermissions();
    const cameraRef = useRef(null);

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
    };

    const captureFrame = async () => {
        if (cameraRef.current) {
            try {
                const photo = await cameraRef.current.takePictureAsync({ quality: 0.8 });
                if (photo && photo.uri) {
                    setCapturedFrames(prev => [...prev, photo.uri]);
                    if (capturedFrames.length + 1 >= 3) {
                        // Captured enough frames, process
                        setCameraVisible(false);
                        processLiveness([...capturedFrames, photo.uri]);
                    }
                }
            } catch (e) {
                Alert.alert('Capture Error', e.message);
            }
        }
    };

    const pickFromGallery = async () => {
        let res = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
            quality: 1,
            allowsEditing: false,
            allowsMultipleSelection: true,
        });
        if (res && !res.canceled && res.assets && res.assets.length > 0) {
            const frames = res.assets.slice(0, 5).map(asset => asset.uri);
            processLiveness(frames);
        }
    };

    const processLiveness = async (frames) => {
        setLoading(true);
        setResult('');

        try {
            const formData = new FormData();
            frames.forEach((uri, index) => {
                formData.append('frames', {
                    uri: uri,
                    name: `frame_${index}.jpg`,
                    type: 'image/jpeg',
                });
            });

            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json',
                },
            });

            let data = {};
            try {
                data = await response.json();
            } catch (e) {
                // non-JSON response
            }

            if (response.ok) {
                const isLive = data.is_live;
                const resultText = `${isLive ? '✅ LIVE' : '❌ SPOOF DETECTED'}\n\nConfidence: ${(data.confidence * 100).toFixed(1)}%\n\nChecks:\n• Motion Score: ${(data.motion_score * 100).toFixed(1)}%\n• Texture Quality: ${(data.texture_score * 100).toFixed(1)}%\n• Consistency: ${(data.consistency_score * 100).toFixed(1)}%\n\nProcessing Time: ${data.processing_time_ms.toFixed(0)}ms\n${data.frames_analyzed} frames analyzed`;
                setResult(resultText);
            } else {
                const detail = data && data.detail ? data.detail : `HTTP ${response.status}`;
                setResult(`Error: ${detail}`);
            }
        } catch (e) {
            setResult(`Connection Error: ${e.message}`);
            Alert.alert('Connection Error', 'Make sure the backend server is running.');
        } finally {
            setLoading(false);
            setCapturedFrames([]);
        }
    };

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView contentContainerStyle={styles.scrollView}>
                <View style={styles.header}>
                    <Text style={styles.title}>Track D - Liveness Detection</Text>
                    <Text style={styles.subtitle}>Anti-Spoof Verification</Text>
                </View>

                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardIcon}>🎥</Text>
                        <Text style={styles.cardTitle}>Multi-Frame Capture</Text>
                    </View>
                    <Text style={styles.cardDescription}>
                        Capture 3-5 frames for motion, texture, and consistency analysis.
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

                    <TouchableOpacity
                        style={[styles.button, styles.buttonSecondary]}
                        onPress={pickFromGallery}
                        disabled={loading}
                    >
                        <Text style={styles.buttonText}>
                             Select from Gallery
                        </Text>
                    </TouchableOpacity>

                    {capturedFrames.length > 0 && (
                        <View style={styles.framesPreview}>
                            <Text style={styles.framesText}>
                                ✓ {capturedFrames.length} frame(s) captured
                            </Text>
                        </View>
                    )}
                </View>

                {cameraVisible && permission?.granted && (
                    <View style={styles.cameraModal}>
                        <CameraView
                            style={styles.cameraView}
                            ref={cameraRef}
                            facing='front'
                        >
                            <View style={styles.cameraOverlay}>
                                <Text style={styles.cameraInstruction}>
                                    Frame {capturedFrames.length + 1}/3
                                    {'\n'}Move slightly between captures
                                </Text>
                                <View style={styles.cameraButtonContainer}>
                                    <TouchableOpacity
                                        style={styles.cameraButton}
                                        onPress={captureFrame}
                                    >
                                        <Text style={styles.cameraButtonText}>Capture</Text>
                                    </TouchableOpacity>
                                    <TouchableOpacity
                                        style={[styles.cameraButton, { backgroundColor: '#FF3B30' }]}
                                        onPress={() => {
                                            setCameraVisible(false);
                                            setCapturedFrames([]);
                                        }}
                                    >
                                        <Text style={styles.cameraButtonText}>Cancel</Text>
                                    </TouchableOpacity>
                                </View>
                            </View>
                        </CameraView>
                    </View>
                )}

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
        padding: 20,
        paddingTop: 20,
    },
    header: {
        alignItems: 'center',
        marginBottom: 30,
        paddingVertical: 20,
    },
    title: {
        fontSize: 26,
        fontWeight: 'bold',
        color: '#000000',
        marginBottom: 5,
        textAlign: 'center',
    },
    subtitle: {
        fontSize: 14,
        color: '#666666',
        textAlign: 'center',
    },
    card: {
        backgroundColor: '#F5F5F5',
        borderRadius: 20,
        padding: 20,
        marginBottom: 20,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
        elevation: 3,
        borderWidth: 1,
        borderColor: '#EEEEEE',
    },
    cardHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 8,
    },
    cardIcon: {
        fontSize: 24,
        marginRight: 10,
    },
    cardTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#000000',
    },
    cardDescription: {
        fontSize: 14,
        color: '#666666',
        marginBottom: 20,
        lineHeight: 20,
    },
    button: {
        paddingVertical: 16,
        borderRadius: 12,
        alignItems: 'center',
        marginBottom: 10,
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
        marginTop: 15,
        padding: 12,
        backgroundColor: '#E8F5E9',
        borderRadius: 8,
    },
    framesText: {
        color: '#2E7D32',
        fontSize: 14,
        fontWeight: '600',
        textAlign: 'center',
    },
    cameraModal: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.95)',
        zIndex: 100,
    },
    cameraView: {
        flex: 1,
    },
    cameraOverlay: {
        flex: 1,
        justifyContent: 'space-between',
        padding: 20,
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
        lineHeight: 22,
    },
    resultCard: {
        borderRadius: 20,
        padding: 25,
        marginVertical: 20,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 5,
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
        fontSize: 50,
        marginBottom: 15,
    },
    resultTitle: {
        fontSize: 22,
        fontWeight: 'bold',
        color: '#000000',
        marginBottom: 15,
        textAlign: 'center',
    },
    resultText: {
        fontSize: 15,
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
