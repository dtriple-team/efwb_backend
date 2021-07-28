<template>
  <div v-if="check.nav.view">
    <v-app-bar color="primary" dark flat class="text-center">
      <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      <v-spacer></v-spacer>
      <v-toolbar-title class="">{{
        $router.history.current.name
      }}</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon>
        <v-icon>mdi-plus</v-icon>
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
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title class="text-h6">
            Menu
          </v-list-item-title>
        </v-list-item-content>
      </v-list-item>
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
        { title: "조회", icon: "mdi-watch", to: "/bandlist" },
        { title: "정보", icon: "mdi-forum", to: "/bandinfo" },
      ],
      check: {
        nav: {
          list: ["Login"],
          view: true,
        },
      },
      searchValue: null,
    };
  },
  methods: {},
  watch: {
    $route(to) {
      console.log(to.name);
      if (this.check.nav.list.includes(to.name)) this.check.nav.view = false;
      else {
        this.check.nav.view = true;
      }
    },
  },
};
</script>
