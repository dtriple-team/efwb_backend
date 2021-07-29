<template>
  <div>
    {{ band.bid + band.name }}
  </div>
</template>

<script>
export default {
  props: {
    bandInfo: {
      type: String,
      default: "",
    },
  },
  data: () => ({
    band: "",
  }),
  mounted() {
    this.changeJson();
  },
  created() {
    // this.check();
  },
  methods: {
    changeJson() {
      this.band = JSON.parse(this.bandInfo);
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
