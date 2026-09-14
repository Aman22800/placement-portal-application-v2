<template>
  <div class="container" style="max-width: 480px; margin-top: 80px;">
    <h2 class="mb-4 text-center">Register as Student</h2>

    <div v-if="message" class="alert" :class="messageType === 'error' ? 'alert-danger' : 'alert-success'">
      {{ message }}
    </div>

    <div class="mb-3">
      <label class="form-label">Email</label>
      <input type="email" class="form-control" v-model="form.email">
    </div>
    <div class="mb-3">
      <label class="form-label">Password</label>
      <input type="password" class="form-control" v-model="form.password">
    </div>
    <div class="mb-3">
      <label class="form-label">Full Name</label>
      <input type="text" class="form-control" v-model="form.name">
    </div>
    <div class="mb-3">
      <label class="form-label">Branch</label>
      <input type="text" class="form-control" v-model="form.branch">
    </div>
    <div class="mb-3">
      <label class="form-label">CGPA</label>
      <input type="number" step="0.1" class="form-control" v-model.number="form.cgpa">
    </div>
    <div class="mb-3">
      <label class="form-label">Graduation Year</label>
      <input type="number" class="form-control" v-model.number="form.year">
    </div>

    <button class="btn btn-success w-100 mb-3" @click="register">Register</button>

    <div class="text-center">
      <router-link to="/">Back to Login</router-link>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'RegisterStudent',
  data() {
    return {
      form: { email: '', password: '', name: '', branch: '', cgpa: null, year: null },
      message: '',
      messageType: 'error'
    }
  },
  methods: {
    async register() {
      this.message = ''
      try {
        const res = await axios.post('/api/register/student', this.form)
        this.message = res.data.message + ' Redirecting to login...'
        this.messageType = 'success'
        setTimeout(() => this.$router.push('/'), 1000)
      } catch (err) {
        this.message = err.response?.data?.error || 'Registration failed'
        this.messageType = 'error'
      }
    }
  }
}
</script>