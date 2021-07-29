<template>
  <v-app>
    <v-main>
      <Menu />
      <router-view></router-view>
    </v-main>
  </v-app>
</template>

<script>
//import HelloWorld from './components/HelloWorld';
import Menu from "./components/Menu.vue";
export default {
  name: "App",
  components: {
    Menu,
  },
  data: () => ({
    viewData: {
      value: true,
    },
  }),
  mounted() {},
  created() {},
  methods: {},
  watch: {
    $route() {},
  },
};
</script>
