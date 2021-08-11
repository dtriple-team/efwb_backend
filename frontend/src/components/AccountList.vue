<template>
  <div>
    <v-data-iterator :items="accounts" :search="search" hide-default-footer>
      <template v-slot:header>
        <v-toolbar dark color="primary" flat>
          <v-text-field
            v-model="search"
            clearable
            flat
            solo-inverted
            hide-details
            label="Search"
            dense
            append-icon="mdi-magnify"
          ></v-text-field>
        </v-toolbar>
      </template>
      <template v-slot:default="props">
        <v-list>
          <template v-for="(account, index) in props.items">
            <v-list-item :key="index" @click="listClick(accounts[index])">
              <!-- <v-list-item-icon class="list-item">
                <v-icon :color="'green'">mdi-circle-medium</v-icon>
              </v-list-item-icon> -->

              <v-list-item-content class="list-item">
                <v-list-item-title v-text="account.uid"></v-list-item-title>
              </v-list-item-content>

              <v-list-item-content class="list-item">
                <v-list-item-title v-text="account.name"></v-list-item-title>
              </v-list-item-content>
              <v-list-item-content class="list-item">
                <v-list-item-title
                  v-text="account.permission"
                ></v-list-item-title>
              </v-list-item-content>
              <v-list-item-content class="list-item">
                <v-list-item-title
                  v-text="account.organization"
                ></v-list-item-title>
              </v-list-item-content>

              <!-- <v-list-item-icon class="list-item">
                <v-btn
                  depressed
                  block
                  class="primary"
                  @click="log(accounts[index])"
                  >조회</v-btn
                >
              </v-list-item-icon> -->
            </v-list-item>
            <v-divider :key="account.uid"></v-divider>
          </template>
        </v-list>
      </template>
    </v-data-iterator>
  </div>
</template>

<script>
export default {
  data: () => ({
    accounts: [
      {
        active: true,
        uid: 10000,
        name: "주강대",
        permission: "admin",
        organization: "디트리플",
      },
      {
        active: true,
        uid: 2000,
        name: "하재",
        permission: "staff",
        organization: "디트리플",
      },
      {
        active: true,
        uid: 3000,
        name: "김갑슨",
        permission: "manager",
        organization: "개인",
      },
    ],
    search: "",
  }),
  methods: {
    listClick(account) {
      console.log(account);
      this.$router.push({
        name: "Account Info",
        params: { account: JSON.stringify(account) },
      });
    },
  },
};
</script>
<style lang="scss">
.list-item {
  align-self: center; // [jk]
}
.list-item.left-margin {
  margin-left: -5px;
}
</style>
