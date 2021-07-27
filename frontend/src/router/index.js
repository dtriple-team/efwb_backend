import Vue from 'vue'
import VueRouter from 'vue-router'
import Main from '@/components/Main'
import BandList from '@/components/BandList'
Vue.use(VueRouter)

const routes = [
    {
        path: '/',
        name: 'Main',
        component: Main
    },
    {
        path: '/band',
        name: 'BandList',
        component: BandList
    },
]

const router = new VueRouter({
    mode: 'history',
    routes
})

export default router