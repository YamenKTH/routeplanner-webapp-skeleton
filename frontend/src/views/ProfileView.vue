<template>
  <div class="profile">
    <div class="profile-header">
      <img class="avatar" src="https://picsum.photos/seed/user/100" />
      <div>
        <h3>@LilOlli</h3>
        <p>Name Lastname</p>
        <p><b>Currently in:</b> Belgrad</p>
      </div>
      <button class="edit-btn">Edit profile</button>
    </div>

    <section class="vibe">
      <h3>My vibe</h3>
      <p>You haven’t finished your profile. Pick a ready-made template or create your own!</p>
      <div class="vibe-buttons">
        <button class="make-own">+ Make my Own</button>
        <button>Nature Lover</button>
        <button>Foodie</button>
        <button>Cultured</button>
        <button>Big Spender</button>
        <button>Family Person</button>
      </div>
    </section>

    <section class="saved">
      <h3>Saved spots</h3>
      <div class="actions">
        <button>CLEAR ALL</button>
        <button>SAVE PRESET</button>
        <button>LOAD PRESET</button>
      </div>
      <div class="spot">
        <img src="https://picsum.photos/id/1043/400/180" />
        <div class="spot-info">
          <h4>Casa Vicens</h4>
          <p>Address 123</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style>
.profile {
  padding: 1rem;
}
.profile-header {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}
.edit-btn {
  margin-left: auto;
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
}
.vibe-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.vibe-buttons button {
  border: none;
  border-radius: 10px;
  padding: 0.6rem;
  font-weight: 500;
  cursor: pointer;
  background: #d6b28c;
  color: white;
}
.make-own {
  background: #3a8063;
}
.saved {
  margin-top: 1.5rem;
}
.actions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.actions button {
  flex: 1;
  border: none;
  border-radius: 10px;
  padding: 0.5rem;
  background: #eee;
  font-weight: 600;
}
.spot {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.spot img {
  width: 100%;
  height: 120px;
  object-fit: cover;
}
.spot-info {
  padding: 0.5rem 1rem;
}
</style>
