/**
 * Delivery confirmation with photo/signature.
 */
import { useState, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, Image, StyleSheet, Alert, ScrollView } from 'react-native';
import { useLocalSearchParams, router, Stack } from 'expo-router';
import SignatureCanvas from 'react-native-signature-canvas';
import * as ImagePicker from 'expo-image-picker';
import { api } from '../../../services/api';

export default function ConfirmDeliveryScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [confirmationType, setConfirmationType] = useState<'photo' | 'signature'>('photo');
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [signatureData, setSignatureData] = useState<string | null>(null);
  const [recipientName, setRecipientName] = useState('');
  const [loading, setLoading] = useState(false);
  const signatureRef = useRef<SignatureCanvas>(null);

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Camera permission is required to take photos');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ['images'],
      quality: 0.7,
      base64: true,
    });

    if (!result.canceled && result.assets[0]) {
      setPhotoUri(result.assets[0].uri);
    }
  };

  const handleSignature = (signature: string) => {
    setSignatureData(signature);
  };

  const clearSignature = () => {
    signatureRef.current?.clearSignature();
    setSignatureData(null);
  };

  const confirmDelivery = async () => {
    if (!id) return;

    const proofData = confirmationType === 'photo'
      ? photoUri || ''
      : signatureData || '';

    if (!proofData) {
      Alert.alert('Error', 'Please provide proof of delivery (photo or signature)');
      return;
    }

    setLoading(true);
    try {
      await api.confirmDelivery(id, confirmationType, proofData, recipientName || undefined);
      Alert.alert('Success', 'Delivery confirmed!', [
        { text: 'OK', onPress: () => router.replace('/(main)/deliveries') }
      ]);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to confirm delivery';
      Alert.alert('Error', message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Stack.Screen options={{ title: 'Confirm Delivery' }} />
      <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
        {/* Tabs */}
        <View style={styles.tabs}>
          <TouchableOpacity
            style={[styles.tab, confirmationType === 'photo' && styles.activeTab]}
            onPress={() => setConfirmationType('photo')}
          >
            <Text style={[styles.tabText, confirmationType === 'photo' && styles.activeTabText]}>
              Photo
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, confirmationType === 'signature' && styles.activeTab]}
            onPress={() => setConfirmationType('signature')}
          >
            <Text style={[styles.tabText, confirmationType === 'signature' && styles.activeTabText]}>
              Signature
            </Text>
          </TouchableOpacity>
        </View>

        {/* Content */}
        <View style={styles.content}>
          {confirmationType === 'photo' ? (
            photoUri ? (
              <View style={styles.photoContainer}>
                <Image source={{ uri: photoUri }} style={styles.photo} resizeMode="cover" />
                <TouchableOpacity style={styles.retakeButton} onPress={takePhoto}>
                  <Text style={styles.retakeText}>Retake Photo</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <TouchableOpacity style={styles.placeholder} onPress={takePhoto}>
                <Text style={styles.placeholderText}>Tap to Take Photo</Text>
                <Text style={styles.placeholderHint}>Take a photo of the delivered order</Text>
              </TouchableOpacity>
            )
          ) : (
            <View style={styles.signatureSection}>
              <View style={styles.signatureContainer}>
                <SignatureCanvas
                  ref={signatureRef}
                  onOK={handleSignature}
                  onEmpty={() => setSignatureData(null)}
                  descriptionText="Customer Signature"
                  clearText="Clear"
                  confirmText="Save"
                  webStyle={`
                    .m-signature-pad { box-shadow: none; border: none; }
                    .m-signature-pad--body { border: none; }
                    .m-signature-pad--footer { display: none; }
                    body, html { background-color: white; }
                  `}
                  autoClear={false}
                  imageType="image/png"
                />
              </View>
              <View style={styles.signatureActions}>
                <TouchableOpacity style={styles.clearButton} onPress={clearSignature}>
                  <Text style={styles.clearText}>Clear</Text>
                </TouchableOpacity>
                {signatureData && (
                  <Text style={styles.signatureSaved}>Signature saved</Text>
                )}
              </View>
            </View>
          )}
        </View>

        {/* Recipient Name */}
        <View style={styles.recipientSection}>
          <Text style={styles.inputLabel}>Recipient Name (optional)</Text>
          <TextInput
            style={styles.input}
            placeholder="Who received the delivery?"
            value={recipientName}
            onChangeText={setRecipientName}
            autoCapitalize="words"
          />
        </View>

        {/* Confirm Button */}
        <TouchableOpacity
          style={[styles.button, (loading || (!photoUri && !signatureData)) && styles.buttonDisabled]}
          onPress={confirmDelivery}
          disabled={loading || (!photoUri && !signatureData)}
        >
          <Text style={styles.buttonText}>
            {loading ? 'Confirming...' : 'Confirm Delivery'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  scrollContent: { padding: 16 },
  tabs: { flexDirection: 'row', marginBottom: 16 },
  tab: {
    flex: 1,
    padding: 12,
    backgroundColor: '#e0e0e0',
    alignItems: 'center',
    borderRadius: 8,
    marginHorizontal: 4,
  },
  activeTab: { backgroundColor: '#4CAF50' },
  tabText: { fontWeight: '600', color: '#666' },
  activeTabText: { color: 'white' },
  content: { minHeight: 300, marginBottom: 16 },
  photoContainer: { flex: 1 },
  photo: { width: '100%', height: 300, borderRadius: 8 },
  retakeButton: {
    backgroundColor: '#FF9800',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  retakeText: { color: 'white', fontWeight: '600' },
  placeholder: {
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#ddd',
    borderStyle: 'dashed',
  },
  placeholderText: { color: '#666', fontSize: 18, fontWeight: '600' },
  placeholderHint: { color: '#999', fontSize: 14, marginTop: 8 },
  signatureSection: { flex: 1 },
  signatureContainer: {
    height: 250,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: 'white',
  },
  signatureActions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  clearButton: {
    backgroundColor: '#FF9800',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  clearText: { color: 'white', fontWeight: '600' },
  signatureSaved: { color: '#4CAF50', fontWeight: '600' },
  recipientSection: { marginBottom: 16 },
  inputLabel: { fontSize: 12, color: '#666', marginBottom: 4 },
  input: {
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    fontSize: 16,
  },
  button: {
    backgroundColor: '#4CAF50',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 20,
  },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
});
