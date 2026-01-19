import React, { useState, useEffect } from 'react';
import { View, Button, Image, Text, ScrollView, StyleSheet, SafeAreaView, ActivityIndicator, Alert, TouchableOpacity } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import * as ImagePicker from 'expo-image-picker';
import { CameraView, useCameraPermissions } from 'expo-camera';

const BACKEND_URL = 'http://10.2.85.122:8000/api/upload_match';

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

function CameraWrapper({ takePhoto, setCameraVisible }) {
  const cameraRef = React.useRef(null);
  return (
    <CameraView
      style={styles.cameraView}
      ref={cameraRef}
      facing="back"
    >
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
    </CameraView>
  );
}

export default function App() {
  const [contactless, setContactless] = useState(null);
  const [contact, setContact] = useState(null);
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const [cameraVisible, setCameraVisible] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();
  const [showMatcher, setShowMatcher] = useState(false);

  const takePhoto = async (cameraRef) => {
    if (cameraRef) {
      const photo = await cameraRef.takePictureAsync({ quality: 1 });
      if (photo && photo.uri) {
        setContactless({ uri: photo.uri });
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
    });
    if (res && !res.canceled && res.assets && res.assets[0]) {
      setImage(res.assets[0]);
      setResult('');
    }
  };

  const sendToBackend = async () => {
    if (!contactless || !contact) {
      Alert.alert('Error', 'Please select both contactless and contact fingerprint images.');
      return;
    }

    setLoading(true);
    setResult('');
    setProcessingStep(PROCESSING_STEPS[0]);

    for (let i = 1; i < PROCESSING_STEPS.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 600));
      setProcessingStep(PROCESSING_STEPS[i]);
    }

    await new Promise(resolve => setTimeout(resolve, 600));

    try {
      const formData = new FormData();
      formData.append('contactless', {
        uri: contactless.uri,
        name: 'contactless.jpg',
        type: 'image/jpeg',
      });
      formData.append('contact', {
        uri: contact.uri,
        name: 'contact.jpg',
        type: 'image/jpeg',
      });

      const response = await fetch(BACKEND_URL, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
      });
      const data = await response.json();
      if (response.ok) {
        const isMatch = data.decision === "MATCH";
        const resultText = `${data.decision}\n\nSimilarity Score: ${(data.score * 100).toFixed(2)}%\nConfidence Level: ${data.confidence}\nProcessing Time: ${data.processing_time_ms}ms\n${data.mode === 'demo' ? '\n⚠️ Demo Mode (Random Scores)' : ''}`;
        setResult(resultText);
      } else {
        setResult(`Error: ${data.detail || 'Unknown error'}`);
      }
    } catch (e) {
      setResult(`Connection Error: ${e.message}`);
      Alert.alert('Connection Error', 'Make sure the backend server is running and the IP address is correct.');
    } finally {
      setLoading(false);
      setProcessingStep('');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={!showMatcher ? styles.scrollViewCentered : styles.scrollView}>
        {!showMatcher ? (
          <View style={styles.homeContainer}>
            <View style={styles.brandingCenter}>
              <Image source={require('./assets/yellowsense_logo.png')} style={styles.brandLogo} />
              <Text style={styles.brandTitle}>YellowSense Technologies</Text>
              <Text style={styles.brandSubtitle}>Advanced Fingerprint Detection</Text>
              <Text style={styles.brandTagline}>Secure • Accurate • Fast</Text>
            </View>
            <TouchableOpacity style={styles.getStartedButton} onPress={() => setShowMatcher(true)}>
              <Text style={styles.getStartedButtonText}>Get Started</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            {/* Back Button */}
            <TouchableOpacity style={styles.backButton} onPress={() => setShowMatcher(false)}>
              <Text style={styles.backButtonText}>← Back</Text>
            </TouchableOpacity>
            
            <View style={styles.header}>
              <Image source={require('./assets/yellowsense_logo.png')} style={styles.brandLogoSmall} />
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

            {cameraVisible && permission?.granted && (
              <View style={styles.cameraModal}>
                <CameraWrapper takePhoto={takePhoto} setCameraVisible={setCameraVisible} />
              </View>
            )}

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
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  homeContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  brandingCenter: {
    alignItems: 'center',
    marginBottom: 50,
  },
  backButton: {
    position: 'absolute',
    top: 20,
    left: 20,
    zIndex: 10,
    padding: 10,
  },
  backButtonText: {
    fontSize: 18,
    color: '#007AFF',
    fontWeight: '600',
  },
  brandLogoSmall: {
    width: 40,
    height: 40,
    resizeMode: 'contain',
    marginBottom: 5,
  },
  brandTitleSmall: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFA500',
    textAlign: 'center',
  },
  getStartedButton: {
    backgroundColor: '#f5c345',
    paddingVertical: 18,
    paddingHorizontal: 50,
    borderRadius: 16,
    shadowColor: '#f5c345',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 5,
  },
  getStartedButtonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  brandLogo: {
    width: 80,
    height: 80,
    resizeMode: 'contain',
    marginBottom: 28, // Increased spacing for better separation
  },
  brandTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFA500',
    marginBottom: 4,
    textAlign: 'center',
  },
  brandSubtitle: {
    fontSize: 15,
    color: '#333',
    textAlign: 'center',
    marginBottom: 4,
  },
  brandTagline: {
    fontSize: 14,
    color: '#007AFF',
    textAlign: 'center',
    marginBottom: 10,
    fontWeight: '500',
  },
  cameraModal: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.95)',
    zIndex: 100,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cameraView: {
    width: '90%',
    height: 400,
    borderRadius: 20,
    overflow: 'hidden',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  cameraButtonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: 20,
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
    padding: 20,
    paddingTop: 20,
  },
  scrollViewCentered: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
    paddingVertical: 5,

  },
  headerIcon: {
    fontSize: 50,
    marginBottom: 10,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#000000',
    marginBottom: 5,
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
    fontSize: 13,
    color: '#666666',
    marginBottom: 15,
  },
  button: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 10,
  },
  buttonPrimary: {
    backgroundColor: '#eab328',
  },
  buttonSecondary: {
    backgroundColor: '#b28405',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  imageContainer: {
    marginTop: 15,
    position: 'relative',
  },
  imagePreview: {
    width: '100%',
    height: 220,
    borderRadius: 12,
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
    marginTop: 15,
    overflow: 'hidden',
  },
  loadingBarFill: {
    height: '100%',
    backgroundColor: '#f5c345',
    width: '70%',
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
    backgroundColor: '#FFEBEE',
    borderColor: '#F44336',
  },
  resultIcon: {
    fontSize: 50,
    marginBottom: 15,
  },
  resultTitle: {
    fontSize: 24,
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
