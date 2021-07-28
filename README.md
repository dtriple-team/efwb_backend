# EFWB

Band Web App

## Quick Start

### 1. Git Clone Project
```
git clone https://github.com/jjaekkaemi/efwb  
```
### 2. Install NPM Module

```
cd frontend
npm install

cd ../backend
npm install
```
### 3. Frontend Build
```
cd frontend
npm run build
```

### 4. Execute & Access
```
cd backend
npm start

> http://localhost:3000/
```
---
## Get Started
### Start Frontend
Create Vue
```
vue create frontend (Version = 2)
```
Install NPM Modules

```
cd frontend
npm install
npm install vue-router(= vue add router)
npm i --save sass-loader@10 node-sass
vue add vuetify
```
Check Vuetify Envirnoment

check `vue.config.js` file
```
npm run serve

  App running at:
  - Local:   http://localhost:8080/
  - Network: http://192.168.0.45:8080/
```
### Start Backend

Install Express
```
express --no-view backend

```
Install NPM Module
```
cd backend
npm install
```
### Connect Frontend to Backend
Edit frontend/vue.config.js

```
const path = require('path')
module.exports = {
  transpileDependencies: [
    'vuetify'
  ],
  outputDir: path.resolve(dirname, '../backend/dist')
}
```
Frontend Build
```
cd frontend
npm run build
```
Edit backend/app.js 'public' -> 'dist'
```
app.use(express.static(path.join(__dirname, 'dist')));
```

Execute & Access
```
cd backend
npm start

> http://localhost:3000/
```