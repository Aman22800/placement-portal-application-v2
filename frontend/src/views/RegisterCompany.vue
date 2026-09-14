<template>
  <div class="container" style="max-width: 480px; margin-top: 80px;">
    <h2 class="mb-4 text-center">Register as Company</h2>

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
      <label class="form-label">Company Name</label>
      <input type="text" class="form-control" v-model="form.company_name">
    </div>
    <div class="mb-3">
      <label class="form-label">HR Contact</label>
      <input type="text" class="form-control" v-model="form.hr_contact">
    </div>
    <div class="mb-3">
      <label class="form-label">Website</label>
      <input type="text" class="form-control" v-model="form.website">
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
  name: 'RegisterCompany',
  data() {
    return {
      form: { email: '', password: '', company_name: '', hr_contact: '', website: '' },
      message: '',
      messageType: 'error'
    }
  },
  methods: {
    async register() {
      this.message = ''
      try {
        const res = await axios.post('/api/register/company', this.form)
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