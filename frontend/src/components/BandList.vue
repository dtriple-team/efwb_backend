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
            <v-list-item action :key="index" @click="listClick(bands[index])">
              <v-list-item-icon class="list-item">
                <v-icon small :color="band.active ? 'secondary' : 'grey'"
                  >mdi-circle</v-icon
                >
              </v-list-item-icon>

              <v-list-item-content class="list-item ml-n5">
                <v-list-item-title
                  class="text-style"
                  v-text="band.bid"
                ></v-list-item-title>
              </v-list-item-content>

              <v-list-item-content class="list-item">
                <v-list-item-title
                  class="text-style"
                  v-text="band.name"
                ></v-list-item-title>
              </v-list-item-content>

              <v-list-item-icon class="list-item">
                <v-icon color="black">
                  mdi-watch-variant
                </v-icon>

                <v-icon v-if="band.rssi > -30" color="black">
                  mdi-signal-cellular-3
                </v-icon>
                <v-icon v-else-if="band.rssi > -50" color="black">
                  mdi-signal-cellular-2
                </v-icon>
                <v-icon v-else-if="band.rssi > -75" color="black">
                  mdi-signal-cellular-1
                </v-icon>
                <v-icon v-else color="black">
                  mdi-signal-cellular-outline
                </v-icon>

                <v-icon v-if="band.battery > 80" color="black">
                  mdi-battery-high
                </v-icon>
                <v-icon v-else-if="band.battery > 40" color="black">
                  mdi-battery-medium
                </v-icon>
                <v-icon v-else-if="band.battery > 15" color="black">
                  mdi-battery-low
                </v-icon>
                <v-icon v-else color="black">
                  mdi-battery-outline
                </v-icon>

                <div class="align-style">{{ band.battery }}%</div>
              </v-list-item-icon>

              <!-- <v-list-item-icon class="list-item">
                <v-btn
                  depressed
                  block
                  class="primary"
                  @click="log(bands[index])"
                  >조회</v-btn
                >
              </v-list-item-icon> -->
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
        battery: 9,
        rssi: -10,
      },
      {
        active: true,
        bid: "0x01",
        name: "Mike",
        scd: true,
        battery: 100,
        rssi: -30,
      },
      {
        active: true,
        bid: "0x02",
        name: "Cindy",
        scd: true,
        battery: 50,
        rssi: -50,
      },
      {
        active: false,
        bid: "0x03",
        name: "Ali",
        scd: true,
        battery: 70,
        rssi: -78,
      },
    ],
    search: "",
  }),
  methods: {
    listClick(band) {
      this.$router.push({
        name: "Band Info",
        params: { bandInfo: JSON.stringify(band) },
      });
    },
  },
};
</script>
<style lang="scss">
.list-item {
  align-self: center; // [jk]
}
.text-style {
  font-size: 1.2rem;
}
.align-style {
  width: 35px;
}
</style>
