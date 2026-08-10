import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { LoginPage } from './auth/LoginPage'
import { PatientListPage } from './patients/PatientListPage'
import { PatientCreatePage } from './patients/PatientCreatePage'
import { PatientDetailPage } from './patients/PatientDetailPage'
import { PatientEditPage } from './patients/PatientEditPage'
import { DoctorListPage } from './doctors/DoctorListPage'
import { DoctorDetailPage } from './doctors/DoctorDetailPage'
import { AppointmentListPage } from './appointments/AppointmentListPage'
import { AppointmentBookingPage } from './appointments/AppointmentBookingPage'
import { EncounterListPage } from './encounters/EncounterListPage'
import { EncounterCreatePage } from './encounters/EncounterCreatePage'
import { EncounterDetailPage } from './encounters/EncounterDetailPage'
import { PatientClinicalHistoryPage } from './encounters/PatientClinicalHistoryPage'
import { LabTestCatalogPage } from './labs/LabTestCatalogPage'
import { LabOrderCreatePage } from './labs/LabOrderCreatePage'
import { LabDashboardPage } from './labs/LabDashboardPage'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/patients"
            element={
              <ProtectedRoute>
                <PatientListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/new"
            element={
              <ProtectedRoute>
                <PatientCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:id"
            element={
              <ProtectedRoute>
                <PatientDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:id/edit"
            element={
              <ProtectedRoute>
                <PatientEditPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patients/:id/clinical-history"
            element={
              <ProtectedRoute>
                <PatientClinicalHistoryPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/doctors"
            element={
              <ProtectedRoute>
                <DoctorListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/doctors/:id"
            element={
              <ProtectedRoute>
                <DoctorDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/appointments"
            element={
              <ProtectedRoute>
                <AppointmentListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/appointments/new"
            element={
              <ProtectedRoute>
                <AppointmentBookingPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/encounters"
            element={
              <ProtectedRoute>
                <EncounterListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/encounters/new"
            element={
              <ProtectedRoute>
                <EncounterCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/encounters/:id"
            element={
              <ProtectedRoute>
                <EncounterDetailPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/lab-tests"
            element={
              <ProtectedRoute>
                <LabTestCatalogPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/lab-orders"
            element={
              <ProtectedRoute>
                <LabDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/lab-orders/new"
            element={
              <ProtectedRoute>
                <LabOrderCreatePage />
              </ProtectedRoute>
            }
          />

          <Route path="/" element={<Navigate to="/patients" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
