import Vue from 'vue'
import Router from 'vue-router'
import home from '@/views/home';
import { isAdmin, isLoggedIn } from '@/lib/auth';

Vue.use(Router)

const router = new Router({
    routes: [
        {
            path: '/',
            redirect: '/page5'
        },
        {
            path: '/login',
            name: 'login',
            component: () => import('@/views/login')
        },
        {
            path: '/register',
            name: 'register',
            component: () => import('@/views/register')
        },
        {
            path: '',
            name: 'home',
            component: home,
            meta: { requiresAuth: true },
            children: [
                {
                    path: '/page1',
                    name: 'page1',
                    component: () => import('@/views/page1')
                },
                {
                    path: '/page2',
                    name: 'page2',
                    component: () => import('@/views/page2')
                },
                {
                    path: '/page3',
                    name: 'page3',
                    component: () => import('@/views/page3')
                },
                {
                    path: '/page4',
                    name: 'page4',
                    component: () => import('@/views/page4')
                },
                {
                    path: '/page5',
                    name: 'page5',
                    component: () => import('@/views/page5')
                },
                {
                    path: '/page6',
                    name: 'page6',
                    component: () => import('@/views/page6')
                },
                {
                    path: '/page7',
                    name: 'page7',
                    component: () => import('@/views/page7')
                },
                {
                    path: '/page8',
                    name: 'page8',
                    component: () => import('@/views/page8')
                },
                {
                    path: '/users',
                    name: 'users',
                    component: () => import('@/views/userManagement'),
                    meta: { requiresAdmin: true }
                }
            ]
        },
        {
            path: '*',
            redirect: '/page5'
        }
    ]
})

router.beforeEach((to, from, next) => {
    const loggedIn = isLoggedIn();
    const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
    const requiresAdmin = to.matched.some((record) => record.meta.requiresAdmin);

    if ((to.path === '/login' || to.path === '/register') && loggedIn) {
        next('/page5');
        return;
    }

    if (requiresAuth && !loggedIn) {
        next({
            path: '/login',
            query: { redirect: to.fullPath }
        });
        return;
    }

    if (requiresAdmin && !isAdmin()) {
        next('/page5');
        return;
    }

    next();
});

export default router
