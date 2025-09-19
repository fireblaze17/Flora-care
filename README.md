# FloraCore - Plant Disease Identification & Care Management System

A comprehensive plant health management platform that combines AI-powered disease detection with intelligent plant care tracking. This project demonstrates advanced computer vision, full-stack web development, and agricultural technology integration.

## 📋 Project Overview

FloraCore is a complete plant management ecosystem that provides:
- **AI Disease Detection**: Deep learning models for identifying plant diseases from images
- **Plant Care Management**: Full-stack web application for tracking plant health and care schedules
- **Business Analytics**: Profit calculation and sales tracking for commercial plant operations
- **Real-time Notifications**: Firebase integration for watering reminders and care alerts

**Key Features:**
- **Computer Vision**: CNN models trained on 32 plant species with disease classification
- **Web Application**: Flask-based platform with user authentication and plant management
- **Database Integration**: MySQL backend for user data and plant records
- **Mobile Responsive**: Progressive web app design for mobile and desktop
- **Firebase Integration**: Push notifications and real-time updates

## 🏗️ System Architecture

### 1. AI/ML Components
- **Disease Detection Models**: TensorFlow/Keras CNN architectures
- **Training Pipeline**: Jupyter notebooks with data preprocessing and model training
- **Model Versions**: Multiple iterations (v1, v2) with performance improvements

### 2. Web Application (Flask Backend)
- **User Authentication**: Secure login/registration system
- **Plant Management**: CRUD operations for plant inventory
- **Care Scheduling**: Automated watering reminders and care tracking
- **Analytics Dashboard**: Business metrics and profit calculations

### 3. Frontend (HTML/CSS/JavaScript)
- **Responsive Design**: Mobile-first approach with modern UI/UX
- **Real-time Updates**: JavaScript integration with Firebase
- **Interactive Forms**: Plant addition, editing, and health monitoring

### 4. Database (MySQL)
- **User Management**: Secure user accounts and session management
- **Plant Records**: Comprehensive plant data with care history
- **Sales Tracking**: Revenue and cost analysis for commercial operations

## 🤖 AI Disease Detection Models

### Dataset & Training
- **Species Coverage**: 32 different plant types including fruits, vegetables, and ornamentals
- **Disease Categories**: Multiple disease classifications per plant species
- **Training Data**: Organized in train/validation/test splits
- **Image Preprocessing**: Standardized input pipeline for model consistency

### Supported Plant Types
```
Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, 
Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, 
Tomato (with various disease classifications)
```

### Disease Classifications
- **Healthy Plants**: Normal, disease-free plant identification
- **Fungal Diseases**: Rust, blight, mildew, and fungal infections
- **Bacterial Infections**: Bacterial spot and other bacterial diseases
- **Viral Diseases**: Mosaic virus and other viral infections
- **Pest Damage**: Insect damage and pest-related issues

### Model Performance
- **Architecture**: Convolutional Neural Networks (CNN)
- **Framework**: TensorFlow/Keras
- **Training**: Multiple epochs with validation monitoring
- **Accuracy**: High classification accuracy across disease categories

## 🌐 Web Application Features

### User Management
- **Registration/Login**: Secure user authentication
- **Session Management**: Persistent user sessions with security
- **Profile Management**: User account settings and preferences

### Plant Care Dashboard
- **Plant Inventory**: Add, edit, and manage plant collections
- **Care Scheduling**: Automated watering and maintenance reminders
- **Health Monitoring**: Disease detection integration with camera input
- **Progress Tracking**: Historical care data and plant growth monitoring

### Business Features
- **Cost Tracking**: Seed, soil, pot, and maintenance cost monitoring
- **Profit Calculation**: Revenue analysis for plant sales
- **Analytics Dashboard**: Visual charts and business metrics
- **Sales Management**: Track plant sales and inventory turnover

### Notification System
- **Firebase Integration**: Real-time push notifications
- **Care Reminders**: Automated watering and care alerts
- **Disease Alerts**: Notifications for detected plant health issues
- **Custom Scheduling**: User-defined notification preferences

## 🚀 Getting Started

### Prerequisites
```bash
# Python dependencies
pip install flask tensorflow keras numpy pandas plotly
pip install pymysql firebase-admin apscheduler

# Database setup
# Install MySQL and create 'userdata' database
```

### Installation & Setup

1. **Clone the repository files** (already completed)

2. **Database Configuration**
   ```sql
   -- Create MySQL database
   CREATE DATABASE userdata;
   
   -- Create tables (see app.py for schema)
   -- Configure database credentials in app.py
   ```

3. **Firebase Setup**
   - Place Firebase credentials in `static/computer-science-ia-floracare-firebase-adminsdk-rm6go-e589ffd970.json`
   - Configure Firebase messaging for notifications

4. **Model Setup**
   - Ensure trained models are available in the project directory
   - Update model paths in the Flask application

### Running the Application

#### 1. Start the Web Server
```bash
cd "Plant disease identifier/flask_attempt"
python app.py
```

#### 2. Access the Web Interface
- Navigate to `http://localhost:5000`
- Register a new account or login
- Start managing your plants!

#### 3. Train New Models (Optional)
```bash
# Run the Jupyter notebooks
jupyter notebook train_plant_disease.ipynb
# or
jupyter notebook train_plant_diseaseV2.ipynb
```

## 📱 User Interface Features

### Homepage Dashboard
- **Plant Overview**: Visual cards showing all managed plants
- **Quick Actions**: Add new plants, check watering schedules
- **Search & Filter**: Find specific plants in large collections
- **Status Indicators**: Visual health status for each plant

### Plant Health Scanner
- **Camera Integration**: Take photos for disease detection
- **AI Analysis**: Real-time disease identification
- **Treatment Recommendations**: Suggested care actions
- **History Tracking**: Record of health scans and treatments

### Analytics & Reports
- **Profit Calculations**: Revenue vs. cost analysis
- **Care Statistics**: Watering frequency and care patterns
- **Growth Tracking**: Plant development over time
- **Business Metrics**: Commercial plant operation insights

## 📁 Project Structure
```
Plant disease identifier/
├── flask_attempt/                    # Web application
│   ├── app.py                       # Flask backend server
│   ├── static/                      # Static assets
│   │   ├── firebase-init.js         # Firebase configuration
│   │   ├── firebase-messaging-sw.js # Service worker
│   │   └── computer-science-ia-...  # Firebase credentials
│   ├── templates/                   # HTML templates
│   │   ├── homepage.html           # Main dashboard
│   │   ├── planthealth.html        # Disease detection interface
│   │   ├── analytics.html          # Business analytics
│   │   ├── login.html              # User authentication
│   │   └── ...                     # Additional pages
│   ├── train_plant_disease.ipynb   # Model training notebook
│   └── train_plant_diseaseV2.ipynb # Improved model version
├── train/                          # Training dataset
│   ├── Apple___Apple_scab/         # Disease categories
│   ├── Apple___Black_rot/          # Organized by plant/disease
│   └── ...                        # 32 plant species
├── valid/                          # Validation dataset
├── test/                           # Test dataset
├── trained_model.h5                # Trained CNN model
├── trained_model_v2.h5             # Improved model version
├── trained_model.keras             # Keras format model
└── weights_for_model.h5            # Model weights
```

## 🛠️ Technical Skills Demonstrated

### Machine Learning & AI
- **Deep Learning**: Custom CNN architectures for image classification
- **Computer Vision**: Agricultural image analysis and disease detection
- **TensorFlow/Keras**: Production-ready model development
- **Model Optimization**: Multiple model versions with performance improvements

### Full-Stack Web Development
- **Backend Development**: Flask API with RESTful endpoints
- **Frontend Design**: Responsive HTML/CSS with modern UI/UX
- **Database Design**: MySQL schema for complex plant management data
- **Authentication**: Secure user management and session handling

### Mobile & Cloud Technologies
- **Progressive Web App**: Mobile-responsive design principles
- **Firebase Integration**: Real-time notifications and cloud services
- **Push Notifications**: Automated care reminders and alerts
- **Cloud Deployment**: Scalable architecture for production deployment

### Agricultural Technology
- **Domain Expertise**: Understanding of plant diseases and care requirements
- **Agricultural AI**: Specialized machine learning for farming applications
- **IoT Integration**: Potential for sensor data integration
- **Precision Agriculture**: Data-driven plant management approaches

### Software Engineering
- **Modular Architecture**: Clean separation of concerns
- **Version Control**: Multiple model iterations and improvements
- **Documentation**: Comprehensive code documentation and user guides
- **Testing**: Model validation and application testing

## 🌱 Agricultural Impact & Applications

### Commercial Agriculture
- **Crop Monitoring**: Early disease detection for large-scale farming
- **Yield Optimization**: Preventive care to maximize crop production
- **Cost Reduction**: Automated monitoring reduces manual inspection costs
- **Quality Assurance**: Consistent disease identification and treatment

### Home Gardening
- **Plant Care Guidance**: Expert-level disease identification for hobbyists
- **Care Automation**: Reminder systems for optimal plant health
- **Learning Platform**: Educational tool for plant disease recognition
- **Community Building**: Shared knowledge and plant care experiences

### Research & Education
- **Agricultural Research**: Data collection for plant disease studies
- **Educational Tool**: Teaching platform for agricultural science
- **Data Analytics**: Large-scale plant health trend analysis
- **Innovation Platform**: Foundation for advanced agricultural AI

## 🔮 Future Enhancements

### AI/ML Improvements
- **Expanded Dataset**: Additional plant species and disease types
- **Multi-modal Analysis**: Integration of environmental sensor data
- **Severity Assessment**: Disease progression tracking and prediction
- **Treatment Efficacy**: Machine learning for treatment outcome prediction

### Application Features
- **IoT Integration**: Automated sensor data collection (moisture, temperature)
- **Mobile App**: Native iOS/Android applications
- **Social Features**: Community sharing and expert consultation
- **Marketplace Integration**: Plant buying/selling platform

### Business Applications
- **Commercial Dashboard**: Enterprise features for large-scale operations
- **Supply Chain Integration**: Seed/fertilizer ordering and inventory management
- **Insurance Integration**: Crop insurance claims and risk assessment
- **Compliance Tracking**: Organic certification and regulatory compliance

## 🎯 Business & Career Impact

This project demonstrates expertise valuable for:
- **Agricultural Technology Companies**: Precision farming and crop monitoring
- **AI/ML Positions**: Computer vision and agricultural AI applications
- **Full-Stack Development**: Complete web application development skills
- **Startup Environment**: End-to-end product development capabilities
- **Research Institutions**: Agricultural AI and plant science applications

---

*FloraCore represents the convergence of artificial intelligence, agricultural science, and modern web development - showcasing the potential of technology to transform traditional farming and plant care into data-driven, intelligent systems.*