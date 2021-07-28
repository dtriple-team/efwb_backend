import Vue from 'vue'
import VueRouter from 'vue-router'
import BandInfo from '@/components/BandInfo'
import BandList from '@/components/BandList'
import Login from '@/components/Login'


Vue.use(VueRouter)

const routes = [
    {
        path:'/login',
        name: 'Login',
        component: Login,
        props: true,
    },
    {
        path: '/bandlist',
        name: 'BAND LIST',
        component: BandList,
        props: true,
    },
    {
        path: '/bandinfo',
        name: 'BAND INFO',
        component: BandInfo
    },
]

const router = new VueRouter({
    mode: 'history',
    routes
})

export default router