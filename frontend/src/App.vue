<template>
  <v-app>
    <v-main>
      <Login v-if="!view" />
      <Menu v-else />
    </v-main>
  </v-app>
</template>

<script>
//import HelloWorld from './components/HelloWorld';
import Login from './components/Login.vue';
import Menu from './components/Menu.vue';
export default {
  name: 'App',
  components: {
    Login,
    Menu
  },
  data: () => ({
    view: true
  }),
};
</script>
