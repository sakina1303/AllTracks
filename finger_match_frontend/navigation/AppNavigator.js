import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import HomeScreen from '../screens/HomeScreen';
import TrackCScreen from '../screens/TrackCScreen';
import TrackDScreen from '../screens/TrackDScreen';

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
    return (
        <Stack.Navigator
            initialRouteName="Home"
            screenOptions={{
                headerStyle: {
                    backgroundColor: '#FFFFFF',
                },
                headerTintColor: '#007AFF',
                headerTitleStyle: {
                    fontWeight: 'bold',
                    fontSize: 18,
                },
                headerShadowVisible: true,
            }}
        >
            <Stack.Screen
                name="Home"
                component={HomeScreen}
                options={{
                    headerShown: false,
                }}
            />
            <Stack.Screen
                name="TrackC"
                component={TrackCScreen}
                options={{
                    title: 'Track C - Fingerprint Matcher',
                }}
            />
            <Stack.Screen
                name="TrackD"
                component={TrackDScreen}
                options={{
                    title: 'Track D - Liveness Detection',
                }}
            />
        </Stack.Navigator>
    );
}
