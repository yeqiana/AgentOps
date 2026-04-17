import { createRouter, createWebHistory } from "vue-router";
import ChatRedesignPage from "../pages/ChatRedesignPage.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/chatgpt-redesign"
    },
    {
      path: "/chatgpt-redesign",
      name: "chatgpt-redesign",
      component: ChatRedesignPage
    }
  ]
});
