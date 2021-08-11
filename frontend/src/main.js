import Vue from "vue";
import App from "./App.vue";
import vuetify from "./plugins/vuetify";
import router from "./router";
import session from "../src/plugins/session.js";

Vue.config.productionTip = false;
Vue.use(session);
new Vue({
  vuetify,
  router,
  render: (h) => h(App),
}).$mount("#app");
