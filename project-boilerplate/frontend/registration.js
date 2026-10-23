// Import the functions you need from the SDKs you need
  import { initializeApp } from "https://www.gstatic.com/firebasejs/13.1.0/firebase-app.js";
  import { getAnalytics } from "https://www.gstatic.com/firebasejs/13.1.0/firebase-analytics.js";
  // TODO: Add SDKs for Firebase products that you want to use
  // https://firebase.google.com/docs/web/setup#available-libraries

  const firebaseConfig = {
    apiKey: "AIzaSyDVPoTYGQ3NXL3CpaH1DRMMZhtrVC8yYe8",
    authDomain: "persona-transformation.firebaseapp.com",
    projectId: "persona-transformation",
    storageBucket: "persona-transformation.firebasestorage.app",
    messagingSenderId: "658372611571",
    appId: "1:658372611571:web:6cba65405807423d169686",
    measurementId: "G-R6W60LJJ9K"
  };

  // Initialize Firebase
  const app = initializeApp(firebaseConfig);
  const analytics = getAnalytics(app);