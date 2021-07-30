<template>
  <div v-if="nav.view">
    <v-app-bar color="primary" dark flat class="text-center">
      <v-app-bar-nav-icon @click.stop="drawer = !drawer">
        <v-icon>
          mdi-circle-slice-8
        </v-icon>
      </v-app-bar-nav-icon>
      <v-spacer></v-spacer>
      <v-toolbar-title
        v-if="appbar()"
        class=" display-1 font-weight-bold text-uppercase"
        >{{ title }}</v-toolbar-title
      >
      <v-spacer></v-spacer>
      <v-btn icon @click="back()">
        <v-icon v-if="appbar()">mdi-plus-thick</v-icon>
        <v-icon v-else>mdi-undo-variant</v-icon>
        <!-- <v-icon>mdi-plus-thick</v-icon> -->
      </v-btn>
      <!-- <template v-slot:extension v-if="check.search.view">
        <v-text-field
          dense
          clearable
          flat
          solo-inverted
          hide-details
          v-model="searchValue"
          append-icon="mdi-magnify"
        ></v-text-field>
      </template> -->
    </v-app-bar>
    <v-navigation-drawer v-model="drawer" absolute temporary>
      <template v-slot:prepend>
        <v-list-item two-line link>
          <v-list-item-avatar color="indigo">
            <span class="white--text text-h5">{{ account.name }}</span>
          </v-list-item-avatar>

          <v-list-item-content>
            <v-list-item-title>{{ account.name }}</v-list-item-title>
            <v-list-item-subtitle>{{
              account.permission
            }}</v-list-item-subtitle>
          </v-list-item-content>
        </v-list-item>
      </template>
      <v-divider></v-divider>

      <v-list-item>
        <v-list-item-content>
          <v-list-item-subtitle>
            Band
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list dense>
        <v-list-item v-for="item in items" :key="item.title" link :to="item.to">
          <v-list-item-icon>
            <v-icon>{{ item.icon }}</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>{{ item.title }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list>
      <template v-slot:append>
        <div class="pa-2">
          <v-btn depressed block class="primary" @click="logout()">
            Logout
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>
  </div>
</template>

<script>
export default {
  name: "Menu",
  props: {
    view: {},
  },
  data() {
    return {
      drawer: null,
      items: [
        { title: "밴드 조회", icon: "mdi-watch-variant", to: "/bandlist" },
        { title: "계정 조회", icon: "mdi-account-circle", to: "/accountlist" },
      ],
      nav: {
        list: ["Login"],
        view: true,
      },
      appbaricon: ["Band Info", "Account Info"],
      account: {
        name: "하재경",
        permission: "관리자",
      },
      searchValue: null,
      title: null,
    };
  },
  methods: {
    init() {
      this.title = this.$router.history.current.name;
      if (this.nav.list.includes(this.title)) this.nav.view = false;
      else this.nav.view = true;
    },
    appbar() {
      if (this.appbaricon.includes(this.title)) return false;
      else return true;
    },
    logout() {
      this.drawer = !this.drawer;
      this.$router.push("/login");
    },
    back() {
      this.$router.go(-1);
    },
  },
  created() {
    this.init();
  },
  watch: {
    $route() {
      this.init();
    },
  },
};
</script>
