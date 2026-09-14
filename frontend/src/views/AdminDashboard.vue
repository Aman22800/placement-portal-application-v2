<template>
  <div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Admin Dashboard</h2>
      <button class="btn btn-outline-secondary btn-sm" @click="logout">Logout</button>
    </div>

    <!-- OVERVIEW STATS -->
    <div class="row mb-4 text-center">
      <div class="col">
        <div class="card"><div class="card-body">
          <h5>{{ stats.total_students ?? '-' }}</h5><small class="text-muted">Students</small>
        </div></div>
      </div>
      <div class="col">
        <div class="card"><div class="card-body">
          <h5>{{ stats.total_companies ?? '-' }}</h5><small class="text-muted">Companies</small>
        </div></div>
      </div>
      <div class="col">
        <div class="card"><div class="card-body">
          <h5>{{ stats.total_drives ?? '-' }}</h5><small class="text-muted">Drives</small>
        </div></div>
      </div>
      <div class="col">
        <div class="card"><div class="card-body">
          <h5>{{ stats.total_applications ?? '-' }}</h5><small class="text-muted">Applications</small>
        </div></div>
      </div>
      <div class="col">
        <div class="card"><div class="card-body">
          <h5>{{ stats.total_placed ?? '-' }}</h5><small class="text-muted">Placed</small>
        </div></div>
      </div>
    </div>

    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <a class="nav-link" :class="{active: tab === 'companies'}" href="#" @click.prevent="tab = 'companies'">Companies</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{active: tab === 'drives'}" href="#" @click.prevent="tab = 'drives'">Drives</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{active: tab === 'students'}" href="#" @click.prevent="tab = 'students'; fetchStudents()">Students</a>
      </li>
    </ul>

    <div v-if="message" class="alert" :class="messageType === 'error' ? 'alert-danger' : 'alert-success'">
      {{ message }}
    </div>

    <!-- COMPANIES TAB -->
    <div v-if="tab === 'companies'">
      <table class="table">
        <thead>
          <tr>
            <th>Company</th><th>HR Contact</th><th>Status</th><th>Blacklisted</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in companies" :key="c.id">
            <td>{{ c.company_name }}</td>
            <td>{{ c.hr_contact }}</td>
            <td>{{ c.approval_status }}</td>
            <td>{{ c.is_blacklisted ? 'Yes' : 'No' }}</td>
            <td>
              <button v-if="c.approval_status !== 'Approved'" class="btn btn-sm btn-outline-success me-1"
                      @click="setCompanyStatus(c.id, 'Approved')">Approve</button>
              <button v-if="c.approval_status !== 'Rejected'" class="btn btn-sm btn-outline-danger me-1"
                      @click="setCompanyStatus(c.id, 'Rejected')">Reject</button>
              <button class="btn btn-sm btn-outline-warning"
                      @click="toggleCompanyBlacklist(c.id, !c.is_blacklisted)">
                {{ c.is_blacklisted ? 'Un-blacklist' : 'Blacklist' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- DRIVES TAB -->
    <div v-if="tab === 'drives'">
      <table class="table">
        <thead>
          <tr>
            <th>Job Title</th><th>Deadline</th><th>Status</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in drives" :key="d.id">
            <td>{{ d.job_title }}</td>
            <td>{{ d.application_deadline }}</td>
            <td>{{ d.status }}</td>
            <td>
              <button v-if="d.status !== 'Approved'" class="btn btn-sm btn-outline-success me-1"
                      @click="setDriveStatus(d.id, 'Approved')">Approve</button>
              <button v-if="d.status !== 'Closed'" class="btn btn-sm btn-outline-danger"
                      @click="setDriveStatus(d.id, 'Closed')">Close</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- STUDENTS TAB -->
    <div v-if="tab === 'students'">
      <table class="table">
        <thead>
          <tr>
            <th>Name</th><th>Email</th><th>Branch</th><th>CGPA</th><th>Year</th>
            <th>Placed</th><th>Blacklisted</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in students" :key="s.id">
            <td>{{ s.name }}</td>
            <td>{{ s.email }}</td>
            <td>{{ s.branch }}</td>
            <td>{{ s.cgpa }}</td>
            <td>{{ s.year }}</td>
            <td>{{ s.is_placed ? 'Yes' : 'No' }}</td>
            <td>{{ s.is_blacklisted ? 'Yes' : 'No' }}</td>
            <td>
              <button class="btn btn-sm btn-outline-warning"
                      @click="toggleStudentBlacklist(s.id, !s.is_blacklisted)">
                {{ s.is_blacklisted ? 'Un-blacklist' : 'Blacklist' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AdminDashboard',
  data() {
    return {
      tab: 'companies',
      companies: [],
      drives: [],
      students: [],
      stats: {},
      message: '',
      messageType: 'error'
    }
  },
  mounted() {
    this.fetchCompanies()
    this.fetchDrives()
    this.fetchStats()
  },
  methods: {
    authHeader() {
      return { headers: { Authorization: `Bearer ${sessionStorage.getItem('token')}` } }
    },

    async fetchStats() {
      try {
        const res = await axios.get('/api/admin/stats', this.authHeader())
        this.stats = res.data
      } catch (err) {
        // stats are non-critical -- fail silently rather than blocking the page
      }
    },

    async fetchCompanies() {
      try {
        const res = await axios.get('/api/admin/companies', this.authHeader())
        this.companies = res.data
      } catch (err) {
        this.message = 'Could not load companies'
        this.messageType = 'error'
      }
    },

    async fetchDrives() {
      try {
        const res = await axios.get('/api/admin/drives', this.authHeader())
        this.drives = res.data
      } catch (err) {
        this.message = 'Could not load drives'
        this.messageType = 'error'
      }
    },

    async fetchStudents() {
      try {
        const res = await axios.get('/api/admin/students', this.authHeader())
        this.students = res.data
      } catch (err) {
        this.message = 'Could not load students'
        this.messageType = 'error'
      }
    },

    async setCompanyStatus(companyId, status) {
      try {
        await axios.put(`/api/admin/companies/${companyId}/status`,
          { approval_status: status }, this.authHeader())
        this.fetchCompanies()
        this.fetchStats()
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not update company'
        this.messageType = 'error'
      }
    },

    async toggleCompanyBlacklist(companyId, newValue) {
      try {
        await axios.put(`/api/admin/companies/${companyId}/blacklist`,
          { is_blacklisted: newValue }, this.authHeader())
        this.fetchCompanies()
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not update blacklist status'
        this.messageType = 'error'
      }
    },

    async toggleStudentBlacklist(studentId, newValue) {
      try {
        await axios.put(`/api/admin/students/${studentId}/blacklist`,
          { is_blacklisted: newValue }, this.authHeader())
        this.fetchStudents()
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not update blacklist status'
        this.messageType = 'error'
      }
    },

    async setDriveStatus(driveId, status) {
      try {
        await axios.put(`/api/admin/drives/${driveId}/status`,
          { status }, this.authHeader())
        this.fetchDrives()
        this.fetchStats()
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not update drive'
        this.messageType = 'error'
      }
    },

    logout() {
      sessionStorage.clear()
      this.$router.push('/')
    }
  }
}
</script>