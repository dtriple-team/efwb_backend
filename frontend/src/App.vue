<template>
  <v-app>
    <v-main>
      <Menu/>
       <router-view v-on:vue-change="viewChange(false)" ></router-view>
    </v-main>
  </v-app>
</template>

<script>
//import HelloWorld from './components/HelloWorld';
import Menu from './components/Menu.vue';
export default {
  name: 'App',
  components: {
    Menu
  },
  data: () => ({
    view: true,
    viewData: {
      value: true
    }
  }),
  mounted() {
    this.viewChange(true)
  },
  created() {

  },
  methods: {
    viewChange(view){
      this.view = view
      if(view) this.$router.push('/login')
      else this.$router.push('/bandlist')
    },
    setView(view){
      this.view = view
    }
  },
    watch: {
      $route() {
      }
    }  
};
</script>
