<template>
  <div>
    <v-data-iterator :items="bands" :search="search" hide-default-footer>
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
          <template v-for="(band, index) in props.items">
            <v-list-item :key="index">
              <v-list-item-icon class="list-item">
                <v-icon :color="'green'">mdi-circle-medium</v-icon>
              </v-list-item-icon>

              <v-list-item-content class="list-item left-margin">
                <v-list-item-title v-text="band.bid"></v-list-item-title>
              </v-list-item-content>

              <v-list-item-content class="list-item">
                <v-list-item-title v-text="band.name"></v-list-item-title>
              </v-list-item-content>
              <v-list-item-icon class="list-item">
                <v-icon :color="band.active ? 'deep-purple accent-4' : 'grey'">
                  mdi-watch-variant
                </v-icon>
              </v-list-item-icon>
              <v-list-item-icon class="list-item">
                <v-icon :color="band.active ? 'deep-purple accent-4' : 'grey'">
                  mdi-battery-high
                </v-icon>
              </v-list-item-icon>
              <v-list-item-icon class="list-item">
                <v-icon :color="band.active ? 'deep-purple accent-4' : 'grey'">
                  mdi-signal-cellular-3
                </v-icon>
              </v-list-item-icon>
              <v-list-item-icon class="list-item">
                <v-btn
                  depressed
                  block
                  class="primary"
                  @click="log(bands[index])"
                  >조회</v-btn
                >
              </v-list-item-icon>
            </v-list-item>
            <v-divider :key="band.bid"></v-divider>
          </template>
        </v-list>
      </template>
    </v-data-iterator>
  </div>
</template>

<script>
export default {
  data: () => ({
    bands: [
      {
        active: true,
        bid: "0x00",
        name: "Jason",
        scd: true,
        battery: 50,
        siganl: -78,
      },
      {
        active: true,
        bid: "0x01",
        name: "Mike",
        scd: true,
        battery: 50,
        siganl: -78,
      },
      {
        active: true,
        bid: "0x02",
        name: "Cindy",
        scd: true,
        battery: 50,
        siganl: -78,
      },
      {
        active: false,
        bid: "0x03",
        name: "Ali",
        scd: true,
        battery: 50,
        siganl: -78,
      },
    ],
    search: "",
  }),
  methods: {
    log(band) {
      this.$router.push("/bandinfo/");
      console.log(band);
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
