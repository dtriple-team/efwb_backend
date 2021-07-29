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

### Frontend

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

### Backend

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

## Use vue-router

### 1. Edit main.js

```
import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import router from './router'

Vue.config.productionTip = false

new Vue({
  vuetify,
  router,
  render: h => h(App)
}).$mount('#app')
```

### 2. Edit index.js

```
import Vue from "vue";
import VueRouter from "vue-router";
import HelloWorld from '@/components/HelloWorld';
Vue.use(VueRouter);

const routes =  [
  {
    path: "/",
    name: "HelloWorld",
    component: HelloWorld
  }
]

const router = new VueRouter({
  mode: "history",
  routes,
});

export default router;
```

### 3. Edit app.js

```
var express = require('express');
var indexRouter = require('./routes/index');

var app = express();
app.use('/', indexRouter);
module.exports = app;
```

### 4. Edit App.vue

```
<template>
  <v-app>
    <v-main>
      <router-view></router-view>
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: "App",
};
</script>

```

#### Show Vue without vue-router

```
<template>
  <v-app>
    <v-main>
      <HelloWorld />
    </v-main>
  </v-app>
</template>

<script>
import HelloWorld from './components/HelloWorld';
export default {
  name: "App",
  components: {
    HelloWorld,
  },
};
</script>
``
```
