const path = require("path");
module.exports = {
  transpileDependencies: ["vuetify"],
  outputDir: path.resolve(__dirname, "../backend/dist"),
  devServer: {
    host: "localhost",
    port: 8080,
    proxy: {
      "^/api": {
        target: "http://localhost:8081",
        changeOrigin: true,
      },
      "^/socket.io": {
        target: "http://localhost:8081",
        changeOrigin: true,
        ws: true,
      },
    },
  },
};
