<template>
  <div class="explore">
    <h2>Explore</h2>
    <div v-for="(place, i) in demoPlaces" :key="i" class="card">
      <img :src="place.img" alt="place image" />
      <div class="info">
        <h3>{{ place.name }}</h3>
        <p>{{ place.address }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
const demoPlaces = [
  { name: "Casa Vicens", address: "Address 123", img: "https://picsum.photos/id/1005/400/200" },
  { name: "Sagrada Familia", address: "Address 321", img: "https://picsum.photos/id/1015/400/200" },
  { name: "Café mamma mia", address: "Address 987", img: "https://picsum.photos/id/1025/400/200" },
  { name: "Casa Mila", address: "Address 555", img: "https://picsum.photos/id/1035/400/200" }
]
</script>

<style>
.explore {
  padding: 1rem;
}
.card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 1rem;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.card img {
  width: 100%;
  height: 140px;
  object-fit: cover;
}
.info {
  padding: 0.5rem 1rem;
}
</style>
