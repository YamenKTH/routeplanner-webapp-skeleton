<template>
  <div class="page-wraper">
    <div class="profile">
      <!-- Header / Profile Card -->
      <div class="profile-header">
        <img class="avatar" src="https://picsum.photos/seed/user/100" alt="Profile picture" />
        <div class="header-info">
          <h3>@LilOlli</h3>
          <p>Name Lastname</p>
          <p><b>Currently in:</b> Belgrad</p>
        </div>
        <button class="edit-btn">Edit profile</button>
      </div>

      <!-- My vibe / Preferences -->
      <section class="vibe">
        <h3>My vibe</h3>
        <p class="subtle">Adjust to personalize your Explore page</p>

        <div class="pref-row" v-for="item in prefs" :key="item.label">
          <div class="left">
            <span class="emoji">{{ item.icon }}</span>
            <span class="label">{{ item.label }}</span>
          </div>

          <div class="right">
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              v-model="item.value"
              class="slider"
            />
            <span class="percent">{{ item.value }}%</span>
          </div>
        </div>
      </section>

      <!-- Saved spots -->
      <section class="saved">
        <h3>Saved spots</h3>
        <div class="actions">
          <button class="btn ghost">CLEAR ALL</button>
          <button class="btn">SAVE PRESET</button>
          <button class="btn">LOAD PRESET</button>
        </div>
      </section>

      <!-- Spacer so content never hides behind bottom nav -->
      <div class="bottom-spacer" aria-hidden="true"></div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from "vue";

const prefs = reactive([
  { label: "Food",         icon: "🍜", value: 75 },
  { label: "Nature",       icon: "🌿", value: 50 },
  { label: "Architecture", icon: "🏛️", value: 60 },
  { label: "Beach",        icon: "🌊", value: 40 },
  { label: "Culture",      icon: "🎭", value: 80 },
]);
</script>

<style>

.page-wraper {
  position: relative;
  width: 100%;
  height: 100dvh;
  overflow: hidden;
}


/* Root container uses a dark gradient to match MapView’s vibe */
.profile {
  padding: 1rem;
  padding-bottom: calc(var(--bottom-nav-h) + 20px);
  /* Deep night gradient with subtle purple/indigo glows */
  background:
    linear-gradient(135deg,#8f85f8 0%,#e78ec4 100%);
  min-height: calc(100vh - var(--bottom-nav-h));
  color: #eef4ff;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
  box-sizing: border-box;
  position: relative;
}

.bottom-spacer {
  height: var(--bottom-nav-h);
  width: 100%;
}

/* --- Profile card: glass + lift so it “sticks out” from the background --- */
.profile-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: linear-gradient(135deg,#20168b 0%,#e78ec4 100%);
  color: #eef4ff;
  backdrop-filter: blur(6px) saturate(120%);
  -webkit-backdrop-filter: blur(6px) saturate(120%);
  padding: 0.9rem;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.12);          /* subtle glass border */
  box-shadow:
    0 8px 30px rgba(0,0,0,0.35),                     /* depth */
    inset 0 0 0 1px rgba(127,102,255,0.08);          /* faint inner glow */
}

/* Small neon accent under the card to make it pop more */
.profile-header::after {
  content: "";
  position: absolute;
  inset: auto 0 auto 0;
  height: 1px;
  margin-top: 0.5rem;
  transform: translateY(calc(100% + 6px));
  background: linear-gradient(90deg, rgba(127,102,255,0), rgba(127,102,255,0.55), rgba(176,108,255,0));
  filter: blur(0.2px);
}

.header-info h3 {
  margin: 0 0 2px;
  font-weight: 800;
  letter-spacing: 0.2px;
}
.header-info p {
  margin: 1px 0;
  color: #cfe2ff;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(255,255,255,0.75);
  box-shadow: 0 6px 18px rgba(0,0,0,0.25);
}

.edit-btn {
  margin-left: auto;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(127,102,255,0.35);
  color: #e8e6ff;
  font-weight: 700;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 160ms ease, transform 120ms ease, border-color 160ms ease;
}
.edit-btn:hover {
  background: rgba(255,255,255,0.12);
  border-color: rgba(176,108,255,0.55);
}
.edit-btn:active {
  transform: translateY(1px);
}

/* --- Sections --- */
.vibe {
  margin-top: 1.5rem;
}
.vibe h3 {
  margin-bottom: 0.35rem;
  letter-spacing: 0.2px;
}
.subtle {
  color: #a9c3ff;
  margin-bottom: 0.9rem;
}

/* Preference rows: semi-glass cards matching MapView components */
.pref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 0.65rem 0.8rem;
  margin-bottom: 0.65rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.18);
  background: linear-gradient(135deg,#20168b 0%,#e78ec388 100%);
}

.left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.emoji {
  font-size: 1.25rem;
}

.label {
  font-weight: 700;
  color: #eaf1ff;
  letter-spacing: 0.2px;
  
}

/* Slider + percentage: reuse MapView gradient hues */
.right {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 55%;
}

.slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  background: linear-gradient(90deg, #7f66ff 0%, #b06cff 100%);
  border-radius: 6px;
  outline: none;
  cursor: pointer;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #7f66ff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.25);
  cursor: pointer;
}
.slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #7f66ff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.25);
  cursor: pointer;
}

.percent {
  min-width: 46px;
  text-align: right;
  font-weight: 800;
  color: #d9e6ff;
}

/* Saved spots */
.saved {
  margin-top: 1.5rem;
}

.actions {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 1rem;
}

.btn {
  flex: 1;
  border: 1px solid rgba(127,102,255,0.35);
  border-radius: 10px;
  padding: 0.55rem 0.7rem;
  background: rgba(255,255,255,0.08);
  color: #eef4ff;
  font-weight: 700;
  letter-spacing: 0.2px;
  cursor: pointer;
  transition: background 160ms ease, border-color 160ms ease, transform 120ms ease;
}
.btn:hover {
  background: rgba(255,255,255,0.12);
  border-color: rgba(176,108,255,0.55);
}
.btn:active {
  transform: translateY(1px);
}

.btn.ghost {
  border-color: rgba(255,255,255,0.16);
  background: rgba(255,255,255,0.04);
}
.btn.ghost:hover {
  background: rgba(255,255,255,0.09);
}
</style>
