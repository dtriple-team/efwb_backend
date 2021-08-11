<template>
  <v-container fluid>
    <v-row class="v-row-image">
      <v-col class="mt-16">
        <div class="white--text text-center display-3 font-weight-bold ">
          WELLO
        </div>
        <div class="title-height " />
      </v-col>
    </v-row>
    <v-row class="mt-10">
      <v-col>
        <v-text-field
          v-model="name"
          label="Username"
          filled
          outlined
        ></v-text-field>
        <v-text-field
          v-model="password"
          label="Password"
          filled
          outlined
          type="password"
        >
        </v-text-field>
        <v-btn depressed block class="primary" @click="submit()"
          >sign in!</v-btn
        >
        <div class="text-normal">Forgot password</div>
      </v-col>
    </v-row>
  </v-container>
</template>
<script>
export default {
  data: () => ({
    name: "",
    password: "",
  }),
  methods: {
    async submit() {
      //this.$emit('vue-change')
      //user 체크, uesr_group, user_band, band, event
      //await this.userCheck();
      this.$router.push({
        name: "Band List",
      });
    },
    clear() {
      this.name = "";
      this.password = "";
      this.select = null;
      this.checkbox = false;
    },
    async userCheck() {
      try {
        const res = await this.$http.get("user_table/" + this.name);
        var user = res.data.data;
        this.$session.user = user;
        this.groupCheck(user);
      } catch (e) {
        alert(e);
      }
    },
    async groupCheck(user) {
      try {
        const res = await this.$http.get("user_table/groupinfo/" + user.id);
        var group = res.data.data;
        this.$session.group = group;
        console.log(group);
        this.$session.groupstr = "";
        for (var i = 0; i < group.length; i++) {
          console.log(group[i].groupname);
          this.$session.groupstr =
            this.$session.groupstr + group[i].groupname + " ";
        }
      } catch (e) {
        console.log(e);
      }
      this.$router.push({
        name: "Band List",
      });
    },
  },
};
</script>
<style lang="scss" scoped>
.text-normal {
  text-align: center;
  color: black;
}
.title-height {
  height: 15vh;
}

.v-row-image {
  background-image: url("../assets/login_background.jpg");
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
}
</style>
