import Vue from "vue";
import VueRouter from "vue-router";
import BandInfo from "@/components/BandInfo";
import BandList from "@/components/BandList";
import Login from "@/components/Login";
import AccountList from "@/components/AccountList";
import AccountInfo from "@/components/AccountInfo";
Vue.use(VueRouter);

const routes = [
  {
    path: "/login",
    name: "Login",
    component: Login,
    props: true,
  },
  {
    path: "/bandlist",
    name: "Band List",
    component: BandList,
    props: true,
  },
  {
    path: "/bandinfo",
    name: "Band Info",
    component: BandInfo,
    props: true,
  },
  {
    path: "/accountlist",
    name: "Account List",
    component: AccountList,
    props: true,
  },
  {
    path: "/accountinfo",
    name: "Account Info",
    component: AccountInfo,
    props: true,
  },
];

const router = new VueRouter({
  mode: "history",
  routes,
});

export default router;
