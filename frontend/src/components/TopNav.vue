<template>
  <nav class="topnav">
    <router-link to="/what-is-x" active-class="active">What is X?</router-link>
    <router-link to="/vision" active-class="active">Our Vision</router-link>
    <router-link to="/about-us" active-class="active">About Us</router-link>
    <router-link to="/app-demo" active-class="active">App Demo</router-link>
  </nav>
</template>

<style>
.topnav {
  display: flex;
  justify-content: center;
  gap: 2rem;
  background: #222;
  color: white;
  padding: 1rem;
  font-weight: 500;
  border-bottom: 2px solid #333;
}
.topnav a {
  color: white;
  text-decoration: none;
  font-size: 1rem;
}
.topnav a:hover {
  color: #90e0ef;
}
.active {
  border-bottom: 2px solid #90e0ef;
  padding-bottom: 4px;
}
</style>
