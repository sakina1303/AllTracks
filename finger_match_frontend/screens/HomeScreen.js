import React from 'react';
import { View, Text, ScrollView, StyleSheet, Image, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialIcons } from '@expo/vector-icons';

export default function HomeScreen({ navigation }) {
  const tracks = [
    {
      id: 'C',
      name: 'Track C',
      description: 'Contactless-to-Contact Matching Demo',
      icon: 'fingerprint',
      route: 'TrackC',
      gradient: ['#4facfe', '#00f2fe'],
    },
    {
      id: 'D',
      name: 'Track D',
      description: 'Liveness / Spoof Heuristic',
      icon: 'visibility',
      route: 'TrackD',
      gradient: ['#43e97b', '#38f9d7'],
    },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Branding Section */}
        <View style={styles.brandingContainer}>
          <Image
            source={require('../assets/yellowsense_logo.png')}
            style={styles.brandLogo}
          />
          <Text style={styles.brandTitle}>YellowSense Technologies</Text>
          <Text style={styles.brandSubtitle}>Advanced Fingerprint Detection</Text>
          <Text style={styles.brandTagline}>Secure • Accurate • Fast</Text>
        </View>

        {/* Tracks Section */}
        <View style={styles.tracksSection}>
          <Text style={styles.sectionTitle}>Select a Track</Text>
          <Text style={styles.sectionSubtitle}>
            Track C: contactless-to-contact matching • Track D: liveness / spoof detection
          </Text>
          <ScrollView
            horizontal={true}
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.tracksScrollContainer}
            decelerationRate="fast"
            snapToInterval={300}
          >
            {tracks.map((track) => (
              <Pressable
                key={track.id}
                style={({ pressed }) => [
                  styles.trackCard,
                  pressed && styles.trackCardPressed,
                ]}
                onPress={() => navigation.navigate(track.route)}
              >
                <View style={styles.trackCardContent}>
                  <MaterialIcons name={track.icon} size={48} color="#f5c345" style={styles.trackIcon} />
                  <Text style={styles.trackName}>{track.name}</Text>
                  <Text style={styles.trackDescription}>{track.description}</Text>
                  <View style={styles.trackBadge}>
                    <Text style={styles.trackBadgeText}>Tap to Open →</Text>
                  </View>
                </View>
              </Pressable>
            ))}
          </ScrollView>
        </View>

        {/* Footer */}
        <Text style={styles.footer}>UIDAI SITAA • Biometric Demo</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollContent: {
    flexGrow: 1,
    paddingVertical: 18,
  },
  brandingContainer: {
    alignItems: 'center',
    paddingTop: 26,
    paddingBottom: 18,
    paddingHorizontal: 20,
  },
  brandLogo: {
    width: 78,
    height: 78,
    resizeMode: 'contain',
    marginBottom: 12,
  },
  brandTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFA500',
    marginBottom: 8,
    textAlign: 'center',
  },
  brandSubtitle: {
    fontSize: 15,
    color: '#333',
    textAlign: 'center',
    marginBottom: 6,
  },
  brandTagline: {
    fontSize: 13,
    color: '#007AFF',
    textAlign: 'center',
    fontWeight: '500',
  },
  tracksSection: {
    marginTop: 12,
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 19,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 6,
    paddingHorizontal: 20,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#666',
    paddingHorizontal: 20,
    marginBottom: 14,
    lineHeight: 16,
  },
  tracksScrollContainer: {
    paddingHorizontal: 20,
    paddingVertical: 6,
  },
  trackCard: {
    width: 270,
    height: 300,
    backgroundColor: '#F5F5F5',
    borderRadius: 20,
    marginRight: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 6,
    borderWidth: 1,
    borderColor: '#EEEEEE',
  },
  trackCardPressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.9,
  },
  trackCardContent: {
    flex: 1,
    padding: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  trackIcon: {
    marginBottom: 15,
  },
  trackName: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 10,
    textAlign: 'center',
  },
  trackDescription: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 15,
    lineHeight: 20,
  },
  trackBadge: {
    backgroundColor: '#f5c345',
    paddingHorizontal: 18,
    paddingVertical: 8,
    borderRadius: 18,
    marginTop: 8,
  },
  trackBadgeText: {
    color: '#FFF',
    fontSize: 13,
    fontWeight: '600',
  },
  footer: {
    color: '#999',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 18,
    marginBottom: 16,
  },
});
