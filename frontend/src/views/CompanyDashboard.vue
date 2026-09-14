<template>
  <div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Company Dashboard</h2>
      <button class="btn btn-outline-secondary btn-sm" @click="logout">Logout</button>
    </div>

    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <a class="nav-link" :class="{active: tab === 'drives'}" href="#" @click.prevent="tab = 'drives'">My Drives</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{active: tab === 'create'}" href="#" @click.prevent="tab = 'create'">Post a Drive</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{active: tab === 'profile'}" href="#" @click.prevent="tab = 'profile'; fetchProfile()">My Profile</a>
      </li>
    </ul>

    <div v-if="message" class="alert" :class="messageType === 'error' ? 'alert-danger' : 'alert-success'">
      {{ message }}
    </div>

    <!-- MY DRIVES TAB -->
    <div v-if="tab === 'drives'">
      <div v-if="drives.length === 0" class="text-muted">You haven't posted any drives yet.</div>

      <div class="card mb-3" v-for="drive in drives" :key="drive.id">
        <div class="card-body">
          <div class="d-flex justify-content-between">
            <h5 class="card-title">{{ drive.job_title }}</h5>
            <span class="badge" :class="drive.status === 'Approved' ? 'bg-success' : 'bg-secondary'">
              {{ drive.status }}
            </span>
          </div>
          <button class="btn btn-outline-primary btn-sm" @click="viewApplicants(drive.id)">
            View Applicants
          </button>

          <table class="table mt-3" v-if="selectedDriveId === drive.id">
            <thead>
              <tr>
                <th>Student</th><th>CGPA</th><th>Status</th><th>Resume</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="app in applicants" :key="app.application_id">
                <td>{{ app.student_name }}</td>
                <td>{{ app.student_cgpa }}</td>
                <td>{{ app.status }}</td>
                <td>
                  <a href="#" @click.prevent="downloadApplicantResume(app.application_id)">Download</a>
                </td>
                <td>
                  <button class="btn btn-sm btn-outline-success me-1" @click="shortlist(app.application_id)">Shortlist</button>
                  <button class="btn btn-sm btn-outline-danger" @click="reject(app.application_id)">Reject</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- POST A DRIVE TAB -->
    <div v-if="tab === 'create'">
      <div class="mb-3">
        <label class="form-label">Job Title</label>
        <input type="text" class="form-control" v-model="newDrive.job_title">
      </div>
      <div class="mb-3">
        <label class="form-label">Description</label>
        <textarea class="form-control" v-model="newDrive.job_description"></textarea>
      </div>
      <div class="mb-3">
        <label class="form-label">Eligible Branch</label>
        <input type="text" class="form-control" v-model="newDrive.eligibility_branch">
      </div>
      <div class="mb-3">
        <label class="form-label">Minimum CGPA</label>
        <input type="number" step="0.1" class="form-control" v-model.number="newDrive.eligibility_min_cgpa">
      </div>
      <div class="mb-3">
        <label class="form-label">Graduation Year</label>
        <input type="number" class="form-control" v-model.number="newDrive.eligibility_year">
      </div>
      <div class="mb-3">
        <label class="form-label">Application Deadline</label>
        <input type="date" class="form-control" v-model="newDrive.application_deadline">
      </div>
      <button class="btn btn-primary" @click="createDrive">Post Drive</button>
    </div>

    <!-- MY PROFILE TAB -->
    <div v-if="tab === 'profile'" style="max-width: 500px;">
      <div class="mb-3">
        <label class="form-label">Email</label>
        <input type="text" class="form-control" :value="profile.email" disabled>
      </div>
      <div class="mb-3">
        <span class="badge" :class="profile.approval_status === 'Approved' ? 'bg-success' : 'bg-secondary'">
          {{ profile.approval_status }}
        </span>
        <span v-if="profile.is_blacklisted" class="badge bg-danger ms-1">Blacklisted</span>
      </div>
      <div class="mb-3">
        <label class="form-label">Company Name</label>
        <input type="text" class="form-control" v-model="profileForm.company_name">
      </div>
      <div class="mb-3">
        <label class="form-label">HR Contact</label>
        <input type="text" class="form-control" v-model="profileForm.hr_contact">
      </div>
      <div class="mb-3">
        <label class="form-label">Website</label>
        <input type="text" class="form-control" v-model="profileForm.website">
      </div>
      <button class="btn btn-primary" @click="saveProfile">Save Profile</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'CompanyDashboard',
  data() {
    return {
      tab: 'drives',
      drives: [],
      applicants: [],
      selectedDriveId: null,
      profile: {},
      profileForm: { company_name: '', hr_contact: '', website: '' },
      newDrive: {
        job_title: '', job_description: '', eligibility_branch: '',
        eligibility_min_cgpa: null, eligibility_year: null, application_deadline: ''
      },
      message: '',
      messageType: 'error'
    }
  },
  mounted() {
    this.fetchDrives()
  },
  methods: {
    authHeader() {
      return { headers: { Authorization: `Bearer ${sessionStorage.getItem('token')}` } }
    },

    async fetchDrives() {
      try {
        const res = await axios.get('/api/company/drives', this.authHeader())
        this.drives = res.data
      } catch (err) {
        this.message = 'Could not load drives'
        this.messageType = 'error'
      }
    },

    async viewApplicants(driveId) {
      this.selectedDriveId = driveId
      try {
        const res = await axios.get(`/api/company/drives/${driveId}/applicants`, this.authHeader())
        this.applicants = res.data
      } catch (err) {
        this.message = 'Could not load applicants'
        this.messageType = 'error'
      }
    },

    async shortlist(applicationId) {
      await this.updateStatus(applicationId, 'Shortlisted')
    },
    async reject(applicationId) {
      await this.updateStatus(applicationId, 'Rejected')
    },
    async updateStatus(applicationId, status) {
      try {
        await axios.put(`/api/company/applications/${applicationId}/status`,
          { status }, this.authHeader())
        this.viewApplicants(this.selectedDriveId)
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not update status'
        this.messageType = 'error'
      }
    },

    async downloadApplicantResume(applicationId) {
      try {
        const res = await axios.get(`/api/company/applications/${applicationId}/resume`, {
          ...this.authHeader(),
          responseType: 'blob'
        })
        const disposition = res.headers['content-disposition'] || ''
        const match = disposition.match(/filename="?([^"]+)"?/)
        const filename = match ? match[1] : 'resume.pdf'

        const url = window.URL.createObjectURL(new Blob([res.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
      } catch (err) {
        this.message = 'Could not download resume (student may not have uploaded one)'
        this.messageType = 'error'
      }
    },

    async createDrive() {
      this.message = ''
      try {
        await axios.post('/api/company/drives', this.newDrive, this.authHeader())
        this.message = 'Drive created, pending admin approval'
        this.messageType = 'success'
        this.tab = 'drives'
        this.fetchDrives()
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not create drive'
        this.messageType = 'error'
      }
    },

    // ---------- PROFILE METHODS ----------
    async fetchProfile() {
      try {
        const res = await axios.get('/api/company/profile', this.authHeader())
        this.profile = res.data
        this.profileForm.company_name = res.data.company_name
        this.profileForm.hr_contact = res.data.hr_contact
        this.profileForm.website = res.data.website
      } catch (err) {
        this.message = 'Could not load profile'
        this.messageType = 'error'
      }
    },

    async saveProfile() {
      this.message = ''
      try {
        await axios.put('/api/company/profile', this.profileForm, this.authHeader())
        this.message = 'Profile updated successfully!'
        this.messageType = 'success'
        this.fetchProfile()
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not update profile'
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