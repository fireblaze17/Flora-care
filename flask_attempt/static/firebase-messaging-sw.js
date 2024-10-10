// Import Firebase scripts
importScripts('https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.10.0/firebase-messaging.js');

// Initialize firebase 
firebase.initializeApp({
    apiKey: "AIzaSyC93TUOkpDwvU5hUQXsY-uYGm4RmkRyhIU",
    authDomain: "computer-science-ia-floracare.firebaseapp.com",
    projectId: "computer-science-ia-floracare",
    storageBucket: "computer-science-ia-floracare.appspot.com",
    messagingSenderId: "683749873930",
    appId: "1:683749873930:web:8a4b5d9a2c1ddb5c1c82f3",
    measurementId: "G-G4FYWE9WYM"
});

//retrieve instance
const messaging = firebase.messaging();

messaging.setBackgroundMessageHandler(function(payload) {
    console.log('[firebase-messaging-sw.js] Received background message ', payload);

    const notificationTitle = payload.notification.title || 'Background Message Title';
    const notificationOptions = {
        body: payload.notification.body || 'Background message body here',
        icon: payload.notification.icon || '/firebase-logo.png'
    };

    return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click event
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('http://127.0.0.1:5001')  // website link 
    );
});
