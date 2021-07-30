<template>
  <v-parallax src="../assets/login_background.png">
    <v-container fluid>
      <v-row>
        <v-col class="mt-16">
          <h1 class="text-center display-3 font-weight-bold">WELLO</h1>
          <v-container class="mt-16" fluid>
            <form class="mt-16">
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
            </form>
          </v-container>
        </v-col>
      </v-row>
    </v-container>
  </v-parallax>
</template>
<script>
export default {
  data: () => ({
    name: "",
    password: "",
  }),
  methods: {
    submit() {
      //this.$emit('vue-change')
      this.$router.push("/bandlist");
    },
    clear() {
      this.$v.$reset();
      this.name = "";
      this.password = "";
      this.select = null;
      this.checkbox = false;
    },
  },
};
</script>
<style lang="scss" scoped>
.text-normal {
  text-align: center;
  color: black;
}
</style>
