import Vue from "vue";
import axios from "axios";
import io from "socket.io-client";
const Http = axios.create({
  baseURL: "http://localhost:8081/api/efwb/v1/",
});

const Session = new Vue({
  methods: {
    onDataHandler(data) {
      this.$emit("data", data);
    },
    onMessageHandler(data) {
      console.log(data);
    },
  },
  created() {
    this.io = io("/receiver", { transports: ["websocket"] });
    this.io.on("message", this.onDataHandler.bind(this));
    this.io.on("efwbsync", this.onDataHandler.bind(this));
  },
  data() {
    return {
      user: "",
      group: "",
      groupstr: "",
    };
  },
});

export default {
  install(Main) {
    Main.prototype.$session = Session;
    Main.prototype.$http = Http;
  },
};
