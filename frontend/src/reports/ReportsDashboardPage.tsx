import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import { StatTile } from './StatTile'
import type {
  AppointmentsReport,
  DoctorPerformanceReport,
  LabsReport,
  PatientsReport,
  RevenueReport,
} from './types'

// Validated categorical palette, slot 1 (blue) - a single hue is correct
// here since every chart on this page has exactly one series; color would
// only need to vary if it encoded a second variable.
const SERIES_COLOR = '#2a78d6'
const GRID_COLOR = '#e1e0d9'
const AXIS_COLOR = '#898781'

export function ReportsDashboardPage() {
  const [patients, setPatients] = useState<PatientsReport | null>(null)
  const [appointments, setAppointments] = useState<AppointmentsReport | null>(null)
  const [labs, setLabs] = useState<LabsReport | null>(null)
  const [revenue, setRevenue] = useState<RevenueReport | null>(null)
  const [doctorPerf, setDoctorPerf] = useState<DoctorPerformanceReport | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api.get<PatientsReport>('/reports/patients'),
      api.get<AppointmentsReport>('/reports/appointments?days=180'),
      api.get<LabsReport>('/reports/labs'),
      api.get<RevenueReport>('/reports/revenue?days=30'),
      api.get<DoctorPerformanceReport>('/reports/doctor-performance'),
    ])
      .then(([p, a, l, r, d]) => {
        setPatients(p)
        setAppointments(a)
        setLabs(l)
        setRevenue(r)
        setDoctorPerf(d)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load reports'))
  }, [])

  if (error) {
    return (
      <Layout>
        <p className="text-sm text-red-600">{error}</p>
      </Layout>
    )
  }

  const loading = !patients || !appointments || !labs || !revenue || !doctorPerf

  return (
    <Layout>
      <h1 className="text-lg font-semibold text-slate-900">Reporting &amp; Analytics</h1>

      {loading && <p className="mt-4 text-sm text-slate-500">Loading...</p>}

      {!loading && (
        <>
          {/* Stat tiles */}
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            <StatTile label="Total Patients" value={patients.total_patients} />
            <StatTile label="Total Appointments" value={appointments.total_appointments} />
            <StatTile
              label="Pending Lab Orders"
              value={labs.orders_by_status.find((s) => s.status === 'PENDING')?.count ?? 0}
            />
            <StatTile label="Completed Lab Tests" value={labs.completed_tests} />
            <StatTile label="Revenue Collected" value={`$${revenue.total_revenue}`} />
          </div>

          {/* Charts */}
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <div className="rounded border border-slate-200 bg-white p-4">
              <h2 className="text-sm font-semibold text-slate-700">
                Upcoming Appointments by Day
              </h2>
              <div className="mt-3 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={appointments.appointments_by_day}>
                    <CartesianGrid stroke={GRID_COLOR} vertical={false} />
                    <XAxis dataKey="day" stroke={AXIS_COLOR} fontSize={12} />
                    <YAxis stroke={AXIS_COLOR} fontSize={12} allowDecimals={false} />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="count"
                      name="Appointments"
                      stroke={SERIES_COLOR}
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded border border-slate-200 bg-white p-4">
              <h2 className="text-sm font-semibold text-slate-700">Patients by Department</h2>
              <div className="mt-3 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={patients.patients_by_department}>
                    <CartesianGrid stroke={GRID_COLOR} vertical={false} />
                    <XAxis dataKey="department" stroke={AXIS_COLOR} fontSize={12} />
                    <YAxis stroke={AXIS_COLOR} fontSize={12} allowDecimals={false} />
                    <Tooltip />
                    <Bar
                      dataKey="patient_count"
                      name="Patients"
                      fill={SERIES_COLOR}
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Doctor performance */}
          <div className="mt-6 rounded border border-slate-200 bg-white p-4">
            <h2 className="text-sm font-semibold text-slate-700">Doctor Performance</h2>
            <div className="mt-3 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={doctorPerf.doctors} layout="vertical" margin={{ left: 24 }}>
                  <CartesianGrid stroke={GRID_COLOR} horizontal={false} />
                  <XAxis type="number" stroke={AXIS_COLOR} fontSize={12} allowDecimals={false} />
                  <YAxis
                    dataKey="name"
                    type="category"
                    stroke={AXIS_COLOR}
                    fontSize={12}
                    width={140}
                  />
                  <Tooltip />
                  <Bar
                    dataKey="appointment_count"
                    name="Appointments"
                    fill={SERIES_COLOR}
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
            {/* Revenue shown as a table column, not a second chart axis -
                mixing two differently-scaled measures on one chart would
                mean a dual-axis chart, which we deliberately avoid. */}
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 text-slate-500">
                  <tr>
                    <th className="py-2 pr-4">Doctor</th>
                    <th className="py-2 pr-4">Department</th>
                    <th className="py-2 pr-4">Appointments</th>
                    <th className="py-2 pr-4">Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {doctorPerf.doctors.map((d) => (
                    <tr key={d.id} className="border-b border-slate-100 last:border-0">
                      <td className="py-2 pr-4">{d.name}</td>
                      <td className="py-2 pr-4">{d.department}</td>
                      <td className="py-2 pr-4">{d.appointment_count}</td>
                      <td className="py-2 pr-4">${d.revenue}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pending lab results - a status list, not a chart */}
          <div className="mt-6 rounded border border-slate-200 bg-white p-4">
            <h2 className="text-sm font-semibold text-slate-700">
              Pending Laboratory Results ({labs.pending_orders.length})
            </h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 text-slate-500">
                  <tr>
                    <th className="py-2 pr-4">Patient</th>
                    <th className="py-2 pr-4">Doctor</th>
                    <th className="py-2 pr-4">Test</th>
                    <th className="py-2 pr-4">Ordered</th>
                  </tr>
                </thead>
                <tbody>
                  {labs.pending_orders.map((o) => (
                    <tr key={o.id} className="border-b border-slate-100 last:border-0">
                      <td className="py-2 pr-4">{o.patient_name}</td>
                      <td className="py-2 pr-4">{o.doctor_name}</td>
                      <td className="py-2 pr-4">{o.test_name}</td>
                      <td className="py-2 pr-4">{new Date(o.ordered_at).toLocaleString()}</td>
                    </tr>
                  ))}
                  {labs.pending_orders.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-6 text-center text-slate-400">
                        No pending lab orders.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </Layout>
  )
}
