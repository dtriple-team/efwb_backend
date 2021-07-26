import Vue from 'vue';
import Vuetify from 'vuetify/lib/framework';

Vue.use(Vuetify);

export default new Vuetify({
    theme: {
        themes: {
            light: {
                primary: '#43E396',
                secondary: '#00AF90',
                white: "#FFFFFF",
                black: "#000000"
            }
        }
    }
});
