// Initialize Firebase
firebase.initializeApp({
    apiKey: "AIzaSyC93TUOkpDwvU5hUQXsY-uYGm4RmkRyhIU",
    authDomain: "computer-science-ia-floracare.firebaseapp.com",
    projectId: "computer-science-ia-floracare",
    storageBucket: "computer-science-ia-floracare.appspot.com",
    messagingSenderId: "683749873930",
    appId: "1:683749873930:web:8a4b5d9a2c1ddb5c1c82f3",
    measurementId: "G-G4FYWE9WYM"
});

const messaging = firebase.messaging();



// Request permission for notifications and get the token
messaging.requestPermission()
    .then(() => {
        console.log('Notification permission granted.');
       
    })
    .then((token) => {
        console.log('FCM Token:', token);
        // Handle the token if needed
        // For example, you can send the token to the server here if needed
    })
    .catch((err) => {
        console.error('Unable to get permission to notify.', err);
    });

// Handle incoming messages when the app is in the foreground
messaging.onMessage((payload) => {
    console.log('Message received. ', payload);

    // Customize notification here
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: payload.notification.icon
    };

    new Notification(notificationTitle, notificationOptions);
});

// Register the service worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/firebase-messaging-sw.js')
    .then(function(registration) {
        console.log('Service Worker registered with scope:', registration.scope);
    }).catch(function(err) {
        console.log('Service Worker registration failed:', err);
    });
}




