<template>
  <div>
    <v-data-iterator
      :items="bands"
      :search="search"
      :no-data-text="nodata"
      hide-default-footer
    >
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
                <v-icon small :color="true ? 'secondary' : 'grey'"
                  >mdi-circle</v-icon
                >
              </v-list-item-icon>

              <v-list-item-content class="list-item ml-n5">
                <v-list-item-title
                  class="text-style"
                  v-text="band.bandinfo.bid"
                ></v-list-item-title>
              </v-list-item-content>

              <v-list-item-content class="list-item">
                <v-list-item-title
                  class="text-style"
                  v-text="band.bandinfo.name"
                ></v-list-item-title>
              </v-list-item-content>

              <v-list-item-icon class="list-item">
                <v-icon color="black">
                  mdi-watch-variant
                </v-icon>

                <v-icon v-if="band.bandvalue.rssi > -30" color="black">
                  mdi-signal-cellular-3
                </v-icon>
                <v-icon v-else-if="band.bandvalue.rssi > -50" color="black">
                  mdi-signal-cellular-2
                </v-icon>
                <v-icon v-else-if="band.bandvalue.rssi > -75" color="black">
                  mdi-signal-cellular-1
                </v-icon>
                <v-icon v-else color="black">
                  mdi-signal-cellular-outline
                </v-icon>

                <v-icon v-if="band.bandvalue.battery > 80" color="black">
                  mdi-battery-high
                </v-icon>
                <v-icon v-else-if="band.bandvalue.battery > 40" color="black">
                  mdi-battery-medium
                </v-icon>
                <v-icon v-else-if="band.bandvalue.battery > 15" color="black">
                  mdi-battery-low
                </v-icon>
                <v-icon v-else color="black">
                  mdi-battery-outline
                </v-icon>

                <div class="align-style">{{ band.bandvalue.battery }}%</div>
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
            <v-divider :key="band.bandinfo.alias"></v-divider>
          </template>
        </v-list>
      </template>
    </v-data-iterator>
  </div>
</template>

<script>
export default {
  // props: {
  //   userInfo: {
  //     type: String,
  //     default: "",
  //   },
  // },
  created() {
    //this.getBandList();
    this.$session.$on("data", this.onDataHandler.bind(this));
  },
  mounted() {
    // this.changeJson();
  },
  data: () => ({
    bands: [
      {
        bandinfo: {
          bid: 1,
          name: "하재경",
          alias: "하재경하재경",
          birth: "1997-09-01",
        },
        bandvalue: {
          battery: 89,
          rssi: -45,
        },
      },
    ],
    search: "",
    nodata: "",
  }),
  methods: {
    // changeJson() {
    //   this.user = JSON.parse(this.userInfo);
    // },
    getBandList() {
      this.$http
        .get("bands/list")
        .then((res) => {
          // console.log(res.data.data);
          var bands = res.data.data;
          for (var i = 0; i < bands.length; i++) {
            console.log(bands[i]);
            this.bands.push({
              bandinfo: bands[i],
              bandvalue: {
                rssi: -80,
              },
            });
          }
        })
        .catch((ex) => {
          console.log(ex);
        });
    },
    onDataHandler(data) {
      for (var i = 0; i < this.bands.length; i++) {
        if (data.shortAddress === this.bands[i].bandinfo.bid) {
          this.bands[i].bandvalue.rssi = data.rssi;
        }
      }
    },
    listClick(band) {
      console.log(band);
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
