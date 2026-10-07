import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity, Bell, BookOpen, CalendarDays, Camera, Check, ChevronRight, ClipboardList, HeartPulse, KeyRound, LayoutDashboard,
  LogOut, Mail, Menu, MessageSquare, Minus, Search, Send, Settings, ShieldCheck, Star, Stethoscope, TrendingDown, TrendingUp, UserPlus, Users, X,
} from 'lucide-react';
import API from './services/api';
import { useAuth } from './context/AuthContext';
import DisclaimerBanner from './components/DisclaimerBanner';

const cx = (...values) => values.filter(Boolean).join(' ');
const dateToday = () => new Date().toISOString().slice(0, 10);
const readError = (error) => error?.response?.data?.detail || error?.message || 'Something went wrong. Please try again.';
const inputClass = 'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-sky-600 focus:ring-2 focus:ring-sky-100';
const buttonClass = 'inline-flex items-center justify-center gap-2 rounded-lg bg-sky-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-800 disabled:cursor-not-allowed disabled:opacity-50';
const secondaryButtonClass = 'inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-sky-600 hover:text-sky-700 disabled:opacity-50';
const publicFileUrl = (fileUrl) => fileUrl?.startsWith('http') ? fileUrl : fileUrl || '';

function UserAvatar({ user, size = 'h-10 w-10', imageClassName = '' }) {
  const [imageUrl, setImageUrl] = useState('');
  const initials = user?.full_name?.split(/\s+/).map((part) => part[0]).slice(0, 2).join('').toUpperCase() || '?';
  useEffect(() => {
    if (!user?.avatar_url || !user?.id) {
      setImageUrl('');
      return undefined;
    }
    let active = true;
    let objectUrl;
    API.get(`/users/${user.id}/avatar`, { responseType: 'blob' })
      .then(({ data }) => {
        objectUrl = URL.createObjectURL(data);
        if (active) setImageUrl(objectUrl);
        else URL.revokeObjectURL(objectUrl);
      })
      .catch(() => { if (active) setImageUrl(''); });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [user?.id, user?.avatar_url]);
  return imageUrl
    ? <img src={imageUrl} alt={`${user.full_name} profile`} className={`${size} shrink-0 rounded-full bg-sky-100 object-cover ${imageClassName}`} />
    : <span aria-label={`${user?.full_name || 'User'} profile photo placeholder`} className={`${size} flex shrink-0 items-center justify-center rounded-full bg-sky-100 text-sm font-bold text-sky-800 ${imageClassName}`}>{initials}</span>;
}

function DoctorAvatar({ doctor }) {
  const [imageUrl, setImageUrl] = useState('');
  const initials = doctor.full_name.split(/\s+/).map((part) => part[0]).slice(0, 2).join('').toUpperCase() || '?';
  useEffect(() => {
    if (!doctor.avatar_url) {
      setImageUrl('');
      return undefined;
    }
    let active = true;
    let objectUrl;
    API.get(doctor.avatar_url, { responseType: 'blob' })
      .then(({ data }) => {
        objectUrl = URL.createObjectURL(data);
        if (active) setImageUrl(objectUrl);
        else URL.revokeObjectURL(objectUrl);
      })
      .catch(() => { if (active) setImageUrl(''); });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [doctor.avatar_url]);
  return imageUrl
    ? <img src={imageUrl} alt={`Dr. ${doctor.full_name} profile`} className="h-16 w-16 shrink-0 rounded-full border-2 border-white object-cover shadow-sm" />
    : <span aria-label={`${doctor.full_name} profile photo placeholder`} className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-sky-100 text-lg font-bold text-sky-800">{initials}</span>;
}

function Field({ label, ...props }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className={inputClass} {...props} /></label>;
}

function Notice({ error, success }) {
  if (!error && !success) return null;
  return <div role="status" className={cx('mb-5 rounded-lg px-4 py-3 text-sm', error ? 'bg-rose-50 text-rose-800' : 'bg-emerald-50 text-emerald-800')}>{error || success}</div>;
}

function ResetPasswordScreen({ token, onComplete }) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('The passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      await API.post('/auth/password/reset', { token, new_password: password });
      onComplete();
    } catch (e) {
      setError(readError(e));
    } finally {
      setBusy(false);
    }
  }

  return <main className="mx-auto grid min-h-[calc(100vh-155px)] max-w-6xl items-center gap-12 px-6 py-12 lg:grid-cols-[1fr_0.85fr]">
    <div className="hidden lg:block"><div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-100 text-sky-700"><HeartPulse size={30} /></div><p className="text-sm font-bold uppercase tracking-wider text-sky-700">MediAssist AI</p><h1 className="mt-3 max-w-lg text-4xl font-bold leading-tight text-slate-900">Secure your account again.</h1><p className="mt-4 max-w-lg leading-7 text-slate-600">Choose a new password to regain access to your healthcare account.</p></div>
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-lg sm:p-8">
      <span className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-sky-50 text-sky-700"><KeyRound size={21} /></span>
      <h2 className="text-2xl font-bold text-slate-900">Choose a new password</h2>
      <p className="mt-1 text-sm text-slate-500">Reset links are one-time use and expire after 30 minutes.</p>
      <form onSubmit={submit} className="mt-6 space-y-4">
        <Field label="New password" type="password" autoComplete="new-password" required minLength="8" maxLength="72" value={password} onChange={(event) => setPassword(event.target.value)} />
        <Field label="Confirm new password" type="password" autoComplete="new-password" required minLength="8" maxLength="72" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} />
        {error && <Notice error={error} />}
        <button className={`${buttonClass} w-full`} disabled={busy}>{busy ? 'Updating password…' : 'Set new password'}</button>
      </form>
    </section>
  </main>;
}

function AuthScreen({ onBack }) {
  const { login, registerPatient, registerDoctor } = useAuth();
  const [mode, setMode] = useState('login');
  const [role, setRole] = useState('patient');
  const [form, setForm] = useState({ full_name: '', email: '', password: '', phone: '', specialization: '', license_number: '', qualification: '', experience_years: 0, consultation_fee: 0, department_id: '' });
  const [departments, setDepartments] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => { API.get('/departments/').then(({ data }) => setDepartments(data)).catch((e) => setError(readError(e))); }, []);
  const update = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  async function submit(event) {
    event.preventDefault();
    setError('');
    setNotice('');
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(form.email, form.password);
      } else if (mode === 'forgot') {
        const { data } = await API.post('/auth/password/forgot', { email: form.email });
        setNotice(data.message);
      } else {
        const base = { full_name: form.full_name, email: form.email, password: form.password, phone: form.phone || null };
        if (role === 'patient') {
          await registerPatient(base);
        } else {
          await registerDoctor({
            ...base,
            profile: {
              specialization: form.specialization,
              license_number: form.license_number,
              experience_years: Number(form.experience_years),
              consultation_fee: Number(form.consultation_fee),
              qualification: form.qualification || null,
              department_id: form.department_id || null,
            },
          });
        }
        await login(form.email, form.password);
      }
    } catch (e) {
      setError(readError(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto grid min-h-[calc(100vh-155px)] max-w-6xl items-center gap-12 px-6 py-12 lg:grid-cols-[1fr_0.85fr]">
      <div className="hidden lg:block">
        <div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-100 text-sky-700"><HeartPulse size={30} /></div>
        <p className="text-sm font-bold uppercase tracking-wider text-sky-700">MediAssist AI</p>
        <h1 className="mt-3 max-w-lg text-4xl font-bold leading-tight text-slate-900">Care management, all in one place.</h1>
        <p className="mt-4 max-w-lg leading-7 text-slate-600">Sign in to manage appointments, health records and care services, or create an account to get started.</p>
        <button onClick={onBack} className={`${secondaryButtonClass} mt-7`}>Back to home</button>
      </div>
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-lg sm:p-8">
        {mode !== 'forgot' && <div className="mb-6 flex gap-2 rounded-xl bg-slate-100 p-1">
          <button onClick={() => { setMode('login'); setError(''); setNotice(''); }} className={cx('flex-1 rounded-lg px-4 py-2.5 text-sm font-semibold', mode === 'login' ? 'bg-white text-sky-800 shadow-sm' : 'text-slate-600')}>Sign in</button>
          <button onClick={() => { setMode('register'); setError(''); setNotice(''); }} className={cx('flex-1 rounded-lg px-4 py-2.5 text-sm font-semibold', mode === 'register' ? 'bg-white text-sky-800 shadow-sm' : 'text-slate-600')}>Create account</button>
        </div>}
        <span className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-sky-50 text-sky-700">{mode === 'forgot' ? <Mail size={21} /> : <HeartPulse size={22} />}</span>
        <h2 className="text-2xl font-bold text-slate-900">{mode === 'login' ? 'Welcome back' : mode === 'forgot' ? 'Reset your password' : 'Create your account'}</h2>
        <p className="mt-1 text-sm text-slate-500">{mode === 'login' ? 'Sign in with your registered email and password.' : mode === 'forgot' ? 'Enter your account email and we’ll send a one-time reset link if it matches an active patient or doctor account.' : 'Register as a patient or healthcare professional.'}</p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          {mode === 'register' && <>
            <div className="grid grid-cols-2 gap-2 rounded-lg bg-slate-50 p-1">
              {['patient', 'doctor'].map((option) => <button type="button" key={option} onClick={() => setRole(option)} className={cx('rounded-md py-2 text-sm font-semibold capitalize', role === option ? 'bg-white text-sky-800 shadow-sm' : 'text-slate-600')}>{option}</button>)}
            </div>
            <Field label="Full name" autoComplete="name" required minLength="2" value={form.full_name} onChange={update('full_name')} />
            <Field label="Phone (optional)" autoComplete="tel" value={form.phone} onChange={update('phone')} />
            {role === 'doctor' && <>
              <Field label="Specialization" required value={form.specialization} onChange={update('specialization')} />
              <Field label="Medical license number" required value={form.license_number} onChange={update('license_number')} />
              <div className="grid grid-cols-2 gap-3">
                <Field label="Years of experience" type="number" min="0" value={form.experience_years} onChange={update('experience_years')} />
                <Field label="Consultation fee" type="number" min="0" step="0.01" value={form.consultation_fee} onChange={update('consultation_fee')} />
              </div>
              <Field label="Qualification (optional)" value={form.qualification} onChange={update('qualification')} />
              <label className="block text-sm font-medium text-slate-700">Department (optional)
                <select className={inputClass} value={form.department_id} onChange={update('department_id')}>
                  <option value="">Select department</option>{departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </label>
            </>}
          </>}
          <Field label="Email address" type="email" autoComplete="email" required value={form.email} onChange={update('email')} />
          {mode !== 'forgot' && <Field label="Password" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required minLength="8" value={form.password} onChange={update('password')} />}
          {error && <Notice error={error} />}
          {notice && <Notice success={notice} />}
          <button className={`${buttonClass} w-full`} disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : mode === 'forgot' ? 'Email reset link' : 'Create account'}</button>
        </form>
        {mode === 'login' && <button type="button" onClick={() => { setMode('forgot'); setError(''); setNotice(''); }} className="mt-4 w-full text-center text-sm font-semibold text-sky-700 hover:text-sky-900">Forgot password?</button>}
        {mode === 'forgot' && <button type="button" onClick={() => { setMode('login'); setError(''); setNotice(''); }} className="mt-4 w-full text-center text-sm font-semibold text-sky-700 hover:text-sky-900">Back to sign in</button>}
      </section>
    </main>
  );
}

function Landing({ onOpen }) {
  const tiles = [
    ['Find a doctor', 'Browse specialties, availability and consultation fees.', Stethoscope, 'doctors'],
    ['Appointments', 'Book a visit and follow its status from your dashboard.', CalendarDays, 'appointments'],
    ['Medical records', 'Keep track of visits, treatment notes and prescriptions.', ClipboardList, 'records'],
    ['Symptom assistant', 'Explore educational guidance and recommended next steps.', Activity, 'symptoms'],
  ];
  return <>
    <section className="bg-gradient-to-br from-sky-950 via-sky-900 to-cyan-800 text-white">
      <div className="mx-auto grid max-w-7xl gap-12 px-6 py-16 md:grid-cols-[1.2fr_0.8fr] md:items-center md:py-24">
        <div><span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm text-sky-100"><ShieldCheck size={17} /> Care information, made more accessible</span>
          <h1 className="mt-6 max-w-3xl text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-6xl">Your health journey, supported in one place.</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-sky-100">Find care, manage appointments, and keep important health information organized with MediAssist AI.</p>
          <button onClick={() => onOpen('doctors')} className="mt-8 inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3 font-semibold text-sky-900 shadow-lg hover:bg-sky-50">Browse doctors <Stethoscope size={18} /></button>
        </div>
        <div className="hidden justify-center md:flex"><div className="flex h-64 w-64 items-center justify-center rounded-full border border-white/20 bg-white/10"><div className="flex h-44 w-44 items-center justify-center rounded-full bg-white text-sky-700"><HeartPulse size={92} strokeWidth={1.5} /></div></div></div>
      </div>
    </section>
    <section className="mx-auto max-w-7xl px-6 py-16">
      <p className="text-sm font-bold uppercase tracking-wider text-sky-700">Care, connected</p><h2 className="mt-2 text-3xl font-bold text-slate-900">Explore the platform</h2>
      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{tiles.map(([title, description, Icon, page]) => <button onClick={() => onOpen(page)} key={title} className="rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:border-sky-300 hover:shadow-md"><span className="flex h-12 w-12 items-center justify-center rounded-xl bg-sky-50 text-sky-700"><Icon size={24} /></span><h3 className="mt-5 font-semibold text-slate-900">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-600">{description}</p></button>)}</div>
    </section>
  </>;
}

function SectionHeading({ title, description, action }) {
  return <div className="mb-7 flex flex-wrap items-end justify-between gap-4"><div><h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{title}</h1><p className="mt-1 text-sm text-slate-500">{description}</p></div>{action}</div>;
}

function Doctors({ canBook, onBook }) {
  const [doctors, setDoctors] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [query, setQuery] = useState('');
  const [specialization, setSpecialization] = useState('');
  const [department, setDepartment] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function search(event) {
    event?.preventDefault();
    setBusy(true); setError('');
    try {
      const params = {};
      if (query) params.query = query;
      if (specialization) params.specialization = specialization;
      if (department) params.department_id = department;
      setDoctors((await API.get('/doctors/', { params })).data);
    } catch (e) { setError(readError(e)); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    API.get('/departments/').then(({ data }) => setDepartments(data)).catch((e) => setError(readError(e)));
    search();
  }, []);
  return <section><SectionHeading title="Doctors" description="Search the doctor directory and view verified credentials." /><form onSubmit={search} className="mb-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:grid-cols-[1fr_1fr_1fr_auto]">
    <label className="relative"><span className="sr-only">Search doctors</span><Search className="absolute left-3 top-3.5 text-slate-400" size={17} /><input className={`${inputClass} pl-9`} placeholder="Name or bio" value={query} onChange={(e) => setQuery(e.target.value)} /></label>
    <input className={inputClass} placeholder="Specialization" value={specialization} onChange={(e) => setSpecialization(e.target.value)} />
    <select className={inputClass} value={department} onChange={(e) => setDepartment(e.target.value)}><option value="">All departments</option>{departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select>
    <button className={buttonClass} disabled={busy}>{busy ? 'Searching…' : 'Search'}</button>
  </form><Notice error={error} />
    {doctors.length ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{doctors.map((d) => <article key={d.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-3"><DoctorAvatar doctor={d} />{d.is_verified ? <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700"><Check size={13} /> Verified</span> : <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">Verification pending</span>}</div><h2 className="mt-4 text-lg font-bold text-slate-900">Dr. {d.full_name}</h2><p className="text-sm text-sky-700">{d.specialization}</p><p className="mt-3 text-sm text-slate-600">{d.department?.name || 'General care'} · {d.experience_years} years experience</p><p className="mt-1 text-sm text-slate-600">{d.qualification || 'Qualification not listed'} · Fee: {d.consultation_fee}</p>{d.bio && <p className="mt-3 line-clamp-2 text-sm leading-6 text-slate-500">{d.bio}</p>}<div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4"><span className={cx('text-xs font-semibold', d.available ? 'text-emerald-700' : 'text-slate-500')}>{d.available ? 'Available for booking' : 'Currently unavailable'}</span><button className={secondaryButtonClass} onClick={() => onBook(d)} disabled={!d.available || !canBook}>{canBook ? 'Book appointment' : 'Patient booking only'}</button></div></article>)}</div> : !busy && !error ? <Empty title="No doctors found" detail="Try changing your search or department filters." /> : null}
  </section>;
}

function BookingModal({ doctor, onClose }) {
  const [date, setDate] = useState(dateToday());
  const [slots, setSlots] = useState([]);
  const [slot, setSlot] = useState(null);
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    setSlot(null); setError('');
    API.get('/appointments/available-slots', { params: { doctor_id: doctor.id, date } })
      .then(({ data }) => setSlots(data)).catch((e) => setError(readError(e)));
  }, [doctor, date]);
  async function submit(event) {
    event.preventDefault(); if (!slot) return;
    setBusy(true); setError('');
    try {
      await API.post('/appointments/', { doctor_id: doctor.id, appointment_date: date, start_time: slot.start_time, end_time: slot.end_time, reason });
      onClose(true);
    } catch (e) { setError(readError(e)); }
    finally { setBusy(false); }
  }
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" role="dialog" aria-modal="true"><form onSubmit={submit} className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
    <div className="flex items-start justify-between"><div><h2 className="text-xl font-bold text-slate-900">Book an appointment</h2><p className="mt-1 text-sm text-slate-500">Dr. {doctor.full_name} · {doctor.specialization}</p></div><button type="button" onClick={() => onClose(false)} aria-label="Close" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X /></button></div>
    <label className="mt-5 block text-sm font-medium text-slate-700">Choose a date<input className={inputClass} type="date" min={dateToday()} value={date} onChange={(e) => setDate(e.target.value)} required /></label>
    <p className="mb-2 mt-5 text-sm font-semibold text-slate-700">Available times</p><div className="grid grid-cols-3 gap-2 sm:grid-cols-4">{slots.filter((s) => s.is_available).map((s) => <button type="button" key={s.start_time} onClick={() => setSlot(s)} className={cx('rounded-lg border px-2 py-2 text-sm', slot?.start_time === s.start_time ? 'border-sky-700 bg-sky-50 text-sky-800' : 'border-slate-200 text-slate-700 hover:border-sky-500')}>{s.start_time.slice(0, 5)}</button>)}</div>
    {slots.length > 0 && !slots.some((s) => s.is_available) && <p className="text-sm text-slate-500">No slots are currently available for this date.</p>}
    <label className="mt-5 block text-sm font-medium text-slate-700">Reason for visit<textarea className={inputClass} rows="3" minLength="3" required value={reason} onChange={(e) => setReason(e.target.value)} /></label>
    <Notice error={error} /><button className={`${buttonClass} mt-5 w-full`} disabled={busy || !slot}>{busy ? 'Booking…' : 'Confirm appointment'}</button>
  </form></div>;
}

function Appointments({ user }) {
  const [appointments, setAppointments] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [busyId, setBusyId] = useState('');
  async function load() {
    try { setAppointments((await API.get('/appointments/my')).data); setError(''); }
    catch (e) { setError(readError(e)); }
  }
  useEffect(() => { load(); }, []);
  async function setStatus(id, status) {
    setBusyId(id); setError(''); setSuccess('');
    try {
      await API.patch(`/appointments/${id}/status`, { status });
      setSuccess(`Appointment ${status}.`); await load();
    } catch (e) { setError(readError(e)); }
    finally { setBusyId(''); }
  }
  return <section><SectionHeading title="Appointments" description={user.role === 'doctor' ? 'Review your patient appointments and update their status.' : 'Review or cancel your scheduled appointments.'} /><Notice error={error} success={success} />
    {appointments.length ? <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white"><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-4">{user.role === 'doctor' ? 'Patient' : 'Doctor'}</th><th className="px-5 py-4">Date & time</th><th className="px-5 py-4">Reason</th><th className="px-5 py-4">Status</th><th className="px-5 py-4">Actions</th></tr></thead><tbody className="divide-y divide-slate-100">{appointments.map((a) => <tr key={a.id}><td className="px-5 py-4 font-medium text-slate-900">{user.role === 'doctor' ? a.patient?.full_name : a.doctor?.full_name}</td><td className="px-5 py-4">{a.appointment_date} · {a.start_time?.slice(0, 5)}</td><td className="max-w-xs px-5 py-4 text-slate-600">{a.reason}</td><td className="px-5 py-4"><Status status={a.status} /></td><td className="px-5 py-4"><div className="flex gap-2">{user.role === 'doctor' && a.status === 'pending' && <><button className="rounded-lg bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700" disabled={busyId === a.id} onClick={() => setStatus(a.id, 'confirmed')}>Confirm</button><button className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700" disabled={busyId === a.id} onClick={() => setStatus(a.id, 'rejected')}>Reject</button></>}{user.role === 'doctor' && a.status === 'confirmed' && <button className={secondaryButtonClass} disabled={busyId === a.id} onClick={() => setStatus(a.id, 'completed')}>Complete</button>}{user.role === 'patient' && ['pending', 'confirmed'].includes(a.status) && <button className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700" disabled={busyId === a.id} onClick={() => setStatus(a.id, 'cancelled')}>Cancel</button>}</div></td></tr>)}</tbody></table></div></div> : !error ? <Empty title="No appointments yet" detail="Appointments you book or receive will appear here." /> : null}
  </section>;
}

function Status({ status }) {
  const style = { pending: 'bg-amber-50 text-amber-700', confirmed: 'bg-sky-50 text-sky-700', completed: 'bg-emerald-50 text-emerald-700', cancelled: 'bg-slate-100 text-slate-600', rejected: 'bg-rose-50 text-rose-700' }[status] || 'bg-slate-100 text-slate-600';
  return <span className={cx('rounded-full px-2.5 py-1 text-xs font-semibold capitalize', style)}>{status}</span>;
}

function Records({ user }) {
  const [records, setRecords] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [patients, setPatients] = useState([]);
  const [patientsLoading, setPatientsLoading] = useState(user.role === 'doctor');
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ patient_id: '', visit_date: dateToday(), symptoms: '', diagnosis: '', treatment: '', notes: '' });
  async function load() {
    try { setRecords((await API.get('/records/my')).data); }
    catch (e) { setError(readError(e)); }
  }
  useEffect(() => {
    load();
    if (user.role === 'doctor') {
      API.get('/records/patients')
        .then(({ data }) => setPatients(data))
        .catch((e) => setError(readError(e)))
        .finally(() => setPatientsLoading(false));
    }
  }, []);
  async function createRecord(event) {
    event.preventDefault();
    if (saving) return;
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await API.post('/records/', { ...form, follow_up_date: null, appointment_id: null, prescriptions: [] });
      setSuccess('Medical record saved successfully.');
      setForm({ patient_id: '', visit_date: dateToday(), symptoms: '', diagnosis: '', treatment: '', notes: '' });
      await load();
    } catch (e) { setError(readError(e)); }
    finally { setSaving(false); }
  }
  return <section><SectionHeading title="Medical records" description="Access visit history, treatment details and prescriptions." /><Notice error={error} success={success} />
    {user.role === 'doctor' && <div className="mb-7 rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="mb-4 font-semibold text-slate-900">Add a patient visit record</h2>
      {patientsLoading
        ? <p role="status" className="rounded-lg bg-sky-50 p-4 text-sm text-sky-800">Loading your appointment patients…</p>
        : patients.length === 0
          ? <p className="rounded-lg bg-amber-50 p-4 text-sm leading-6 text-amber-900">There are no patients linked to your account yet. Patients appear here after they book an appointment with you. Once an appointment exists, you can add the visit record from this form.</p>
          : <form onSubmit={createRecord}>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700">Patient<select className={inputClass} required value={form.patient_id} onChange={(e) => setForm({ ...form, patient_id: e.target.value })}><option value="">Select patient</option>{patients.map((p) => <option key={p.id} value={p.id}>{p.full_name} · {p.email}</option>)}</select></label>
              <Field label="Visit date" type="date" required value={form.visit_date} onChange={(e) => setForm({ ...form, visit_date: e.target.value })}/>
              {['symptoms', 'diagnosis', 'treatment'].map((key) => <Field key={key} label={key[0].toUpperCase() + key.slice(1)} required minLength="3" value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />)}
              <label className="block text-sm font-medium text-slate-700 sm:col-span-2">Notes<textarea className={inputClass} rows="2" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label>
            </div>
            <button className={`${buttonClass} mt-4`} disabled={saving || patientsLoading}>{saving ? 'Saving medical record…' : 'Save medical record'}</button>
          </form>}
    </div>}
    {records.length ? <div className="space-y-4">{records.map((r) => <article key={r.id} className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap justify-between gap-2"><h2 className="font-semibold text-slate-900">Visit · {r.visit_date}</h2><span className="text-sm text-slate-500">{user.role === 'patient' ? `Dr. ${r.doctor?.full_name || ''}` : `Patient: ${r.patient?.full_name || ''}`}</span></div><div className="mt-4 grid gap-3 sm:grid-cols-3"><div><p className="text-xs font-semibold uppercase text-slate-500">Symptoms</p><p className="mt-1 text-sm">{r.symptoms}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Diagnosis</p><p className="mt-1 text-sm">{r.diagnosis}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Treatment</p><p className="mt-1 text-sm">{r.treatment}</p></div></div>{r.notes && <p className="mt-4 text-sm text-slate-600">{r.notes}</p>}{r.prescriptions?.length > 0 && <div className="mt-4 border-t pt-4"><p className="font-semibold text-slate-800">Prescriptions</p>{r.prescriptions.map((p) => <p key={p.id} className="mt-1 text-sm text-slate-600">{p.medicine_name} · {p.dosage} · {p.frequency} · {p.duration}</p>)}</div>}</article>)}</div> : !error ? <Empty title="No records available" detail="Your medical visit records and prescriptions will appear here." /> : null}
  </section>;
}

function Profile({ user }) {
  const { refreshUser } = useAuth();
  const isDoctor = user.role === 'doctor';
  const isAdmin = user.role === 'admin';
  const original = isDoctor ? user.doctor_profile || {} : user.patient_profile || {};
  const [departments, setDepartments] = useState([]);
  const [avatarBusy, setAvatarBusy] = useState(false);
  const [avatarError, setAvatarError] = useState('');
  const [form, setForm] = useState(isDoctor
    ? { specialization: original.specialization || '', experience_years: original.experience_years ?? 0, qualification: original.qualification || '', consultation_fee: original.consultation_fee ?? 0, bio: original.bio || '', department_id: original.department_id || '' }
    : { date_of_birth: original.date_of_birth || '', gender: original.gender || '', blood_group: original.blood_group || '', emergency_contact: original.emergency_contact || '', address: original.address || '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (isDoctor) API.get('/departments/').then(({ data }) => setDepartments(data)).catch((e) => setError(readError(e)));
  }, [isDoctor]);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError(''); setSuccess('');
    const payload = isDoctor
      ? { ...form, experience_years: Number(form.experience_years), consultation_fee: Number(form.consultation_fee), department_id: form.department_id || null }
      : { ...form, date_of_birth: form.date_of_birth || null };
    try {
      await API.put(`/users/me/profile/${isDoctor ? 'doctor' : 'patient'}`, payload);
      setSuccess('Profile saved.');
    } catch (e) { setError(readError(e)); }
    finally { setBusy(false); }
  }
  async function uploadAvatar(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setAvatarError('');
    setAvatarBusy(true);
    try {
      const body = new FormData();
      body.append('file', file);
      await API.post('/users/me/avatar', body, { headers: { 'Content-Type': 'multipart/form-data' } });
      await refreshUser();
    } catch (e) { setAvatarError(readError(e)); }
    finally { setAvatarBusy(false); }
  }
  async function removeAvatar() {
    setAvatarError('');
    setAvatarBusy(true);
    try {
      await API.delete('/users/me/avatar');
      await refreshUser();
    } catch (e) { setAvatarError(readError(e)); }
    finally { setAvatarBusy(false); }
  }
  const fields = isDoctor
    ? [['specialization', 'Specialization'], ['experience_years', 'Years of experience'], ['qualification', 'Qualification'], ['consultation_fee', 'Consultation fee'], ['bio', 'Professional bio']]
    : [['gender', 'Gender'], ['blood_group', 'Blood group'], ['emergency_contact', 'Emergency contact'], ['address', 'Address']];
  return <section><SectionHeading title="My profile" description={isAdmin ? 'Manage your administrator account photo.' : `Manage your ${isDoctor ? 'professional' : 'patient'} profile information.`} /><Notice error={error} success={success} />
    <div className="mb-5 flex flex-wrap items-center gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <UserAvatar user={user} size="h-20 w-20" imageClassName="text-xl ring-4 ring-sky-50" />
      <div className="min-w-0 flex-1"><p className="truncate text-lg font-bold text-slate-900">{user.full_name}</p><p className="truncate text-sm text-slate-500">{user.email}</p><p className="mt-1 text-xs capitalize text-slate-500">{user.role} account · JPG, PNG or WebP, up to 2 MB</p>{avatarError && <p role="alert" className="mt-2 text-sm text-rose-700">{avatarError}</p>}</div>
      <div className="flex flex-wrap gap-2">
        <label className={cx(buttonClass, 'cursor-pointer', avatarBusy && 'pointer-events-none opacity-60')}><Camera size={16} />{avatarBusy ? 'Uploading…' : user.avatar_url ? 'Change photo' : 'Upload photo'}<input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" disabled={avatarBusy} onChange={uploadAvatar} /></label>
        {user.avatar_url && <button type="button" className={secondaryButtonClass} onClick={removeAvatar} disabled={avatarBusy}>Remove</button>}
      </div>
    </div>
    {!isAdmin && <form onSubmit={submit} className="max-w-3xl rounded-2xl border border-slate-200 bg-white p-5 sm:p-6"><div className="mb-4"><h3 className="font-bold text-slate-900">Profile details</h3><p className="mt-1 text-sm text-slate-500">{user.full_name} · {user.email}{user.phone && ` · ${user.phone}`}</p></div><div className="grid gap-4 sm:grid-cols-2">
      {isDoctor && <Field label="Specialization" required value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} />}
      {isDoctor && <Field label="Years of experience" type="number" min="0" value={form.experience_years} onChange={(e) => setForm({ ...form, experience_years: e.target.value })} />}
      {isDoctor && <Field label="Qualification" value={form.qualification} onChange={(e) => setForm({ ...form, qualification: e.target.value })} />}
      {isDoctor && <Field label="Consultation fee" type="number" min="0" step="0.01" value={form.consultation_fee} onChange={(e) => setForm({ ...form, consultation_fee: e.target.value })} />}
      {isDoctor && <label className="block text-sm font-medium text-slate-700">Department<select className={inputClass} value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value })}><option value="">No department</option>{departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></label>}
      {!isDoctor && <Field label="Date of birth" type="date" value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} />}
      {fields.filter(([key]) => !isDoctor || !['specialization', 'experience_years', 'qualification', 'consultation_fee'].includes(key)).map(([key, label]) => key === 'bio' || key === 'address'
        ? <label key={key} className="block text-sm font-medium text-slate-700 sm:col-span-2">{label}<textarea className={inputClass} rows="3" value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} /></label>
        : <Field key={key} label={label} value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />)}
    </div><button className={`${buttonClass} mt-5`} disabled={busy}>{busy ? 'Saving…' : 'Save profile'}</button></form>}
  </section>;
}

function Symptoms({ onOpen }) {
  const [form, setForm] = useState({ symptoms: '', duration_days: '', age: '', gender: '', existing_conditions: '' });
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const priorityTone = {
    EMERGENCY: 'border-rose-200 bg-rose-50 text-rose-900',
    HIGH: 'border-orange-200 bg-orange-50 text-orange-950',
    MODERATE: 'border-amber-200 bg-amber-50 text-amber-950',
    LOW: 'border-emerald-200 bg-emerald-50 text-emerald-950',
  };
  const priorityIconTone = {
    EMERGENCY: 'bg-rose-100 text-rose-700',
    HIGH: 'bg-orange-100 text-orange-700',
    MODERATE: 'bg-amber-100 text-amber-700',
    LOW: 'bg-emerald-100 text-emerald-700',
  };
  const followUpPrompts = [
    'How long have these symptoms been present, and are they improving or worsening?',
    'Have you noticed a fever, cough, or any change in your breathing?',
    'Are there other symptoms or existing health conditions a clinician should know about?',
  ];
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError(''); setResult(null);
    try {
      const payload = { symptoms: form.symptoms, duration_days: form.duration_days === '' ? null : Number(form.duration_days), age: form.age === '' ? null : Number(form.age), gender: form.gender || null, existing_conditions: form.existing_conditions ? form.existing_conditions.split(',').map((s) => s.trim()).filter(Boolean) : [] };
      setResult((await API.post('/ai/symptom-check', payload)).data);
    } catch (e) { setError(readError(e)); }
    finally { setBusy(false); }
  }
  const priority = result?.priority_level?.toUpperCase() || 'LOW';
  return <section className="space-y-6">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-sky-100 text-sky-700"><HeartPulse size={25} /></span>
        <div><p className="text-xs font-bold uppercase tracking-[0.16em] text-sky-700">MediAssist AI</p><h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">AI Symptom Assistant</h2><p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">Share what you’re experiencing to see educational information, possible areas of concern, and suggested next steps.</p></div>
      </div>
      <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600"><ShieldCheck size={15} className="text-emerald-600" /> Private health guidance</span>
    </div>
    <div className="rounded-xl border border-sky-100 bg-sky-50/80 px-4 py-3 text-sm leading-6 text-sky-950"><strong>Please note:</strong> This assistant provides educational decision support only. It cannot diagnose a condition or replace advice from a licensed healthcare professional. If you may be experiencing an emergency, contact your local emergency services now.</div>
    <Notice error={error} />
    <div className="grid items-start gap-6 xl:grid-cols-[minmax(300px,0.82fr)_minmax(0,1.18fr)]">
      <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="mb-5"><h3 className="font-bold text-slate-900">Tell us what’s going on</h3><p className="mt-1 text-sm leading-5 text-slate-500">Specific details help provide more relevant general guidance.</p></div>
        <label className="block text-sm font-semibold text-slate-700">Describe your symptoms<textarea className={inputClass} rows="5" minLength="5" required value={form.symptoms} onChange={(e) => setForm({ ...form, symptoms: e.target.value })} placeholder="For example: I have had a sore throat and a cough since yesterday…" /></label>
        <p className="mt-2 text-xs leading-5 text-slate-500">Include when they started, how they have changed, and anything that makes them better or worse.</p>
        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Duration (days)" type="number" min="0" value={form.duration_days} onChange={(e) => setForm({ ...form, duration_days: e.target.value })} />
          <Field label="Age (optional)" type="number" min="0" max="120" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} />
          <Field label="Gender (optional)" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })} />
          <Field label="Existing conditions (optional)" value={form.existing_conditions} onChange={(e) => setForm({ ...form, existing_conditions: e.target.value })} />
        </div>
        <button className={`${buttonClass} mt-5 w-full`} disabled={busy}>{busy ? <><Activity size={16} className="animate-pulse" /> Reviewing your information…</> : <><HeartPulse size={17} /> Review symptoms</>}</button>
        <p className="mt-3 text-center text-xs text-slate-500">Only share information you’re comfortable including.</p>
      </form>
      {result ? <div className="space-y-4" aria-live="polite">
        <article className={cx('rounded-2xl border p-5 shadow-sm sm:p-6', priorityTone[priority] || 'border-slate-200 bg-white text-slate-900')}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3"><span className={cx('flex h-10 w-10 items-center justify-center rounded-xl', priorityIconTone[priority] || 'bg-slate-100 text-slate-700')}><Activity size={20} /></span><div><p className="text-xs font-semibold uppercase tracking-wider opacity-70">Urgency level</p><h3 className="mt-0.5 text-lg font-bold">{priority.charAt(0) + priority.slice(1).toLowerCase()}</h3></div></div>
            {result.is_emergency && <span className="rounded-full bg-rose-600 px-3 py-1 text-xs font-bold text-white">Seek emergency help now</span>}
          </div>
          <p className="mt-4 text-sm leading-6">{result.urgency_recommendation}</p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div><p className="text-xs font-bold uppercase tracking-wider text-sky-700">Your information</p><h3 className="mt-1 text-lg font-bold text-slate-900">Guidance summary</h3></div>
          <p className="mt-3 text-sm leading-6 text-slate-700">{result.summary}</p>
          {result.detected_symptoms?.length > 0 && <div className="mt-4"><h4 className="text-sm font-semibold text-slate-800">Symptoms recognized</h4><div className="mt-2 flex flex-wrap gap-2">{result.detected_symptoms.map((symptom) => <span key={symptom} className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700">{symptom}</span>)}</div></div>}
        </article>
        {!result.is_emergency && result.possible_areas_of_concern?.length > 0 && <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex items-start justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-sky-700">Educational possibilities</p><h3 className="mt-1 text-lg font-bold text-slate-900">Possible areas of concern</h3></div><span className="rounded-lg bg-sky-50 p-2 text-sky-700"><Stethoscope size={19} /></span></div>
          <p className="mt-1 text-xs leading-5 text-slate-500">These are not diagnoses. A clinician can assess your symptoms and determine what may be causing them.</p>
          <div className="mt-4 space-y-3">{result.possible_areas_of_concern.map((concern) => <div key={concern.condition_name} className="rounded-xl border border-slate-100 bg-slate-50/70 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2"><h4 className="font-semibold text-slate-900">{concern.condition_name}</h4><span className="inline-flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600"><Stethoscope size={13} className="text-sky-700" />{concern.recommended_specialty}</span></div>
            <p className="mt-2 text-sm leading-5 text-slate-600">{concern.description}</p>
            <p className="mt-2 border-l-2 border-sky-200 pl-3 text-sm leading-5 text-slate-700">{concern.educational_summary}</p>
          </div>)}</div>
          {result.suggested_department && <button onClick={() => onOpen('doctors')} className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-sky-700 hover:text-sky-900">Browse {result.suggested_department} doctors <ChevronRight size={16} /></button>}
        </article>}
        {result.recommended_next_steps?.length > 0 && <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><p className="text-xs font-bold uppercase tracking-wider text-sky-700">What you can do next</p><h3 className="mt-1 text-lg font-bold text-slate-900">Recommended next steps</h3><ol className="mt-4 space-y-3">{result.recommended_next_steps.map((step, index) => <li key={`${index}-${step}`} className="flex items-start gap-3 text-sm leading-6 text-slate-700"><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xs font-bold text-sky-800">{index + 1}</span><span>{step}</span></li>)}</ol></article>}
        {!result.is_emergency && <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><div className="flex items-center gap-2"><span className="rounded-lg bg-violet-50 p-2 text-violet-700"><Activity size={18} /></span><h3 className="font-bold text-slate-900">Details that may help a clinician</h3></div><p className="mt-2 text-sm text-slate-500">If relevant, note these details before a medical appointment:</p><div className="mt-3 flex flex-wrap gap-2">{followUpPrompts.map((prompt) => <span key={prompt} className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs leading-4 text-slate-600">{prompt}</span>)}</div></article>}
        <p className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs leading-5 text-slate-600">{result.disclaimer}</p>
      </div> : <aside className="space-y-4">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-50 text-sky-700"><ShieldCheck size={21} /></span><h3 className="mt-4 font-bold text-slate-900">What this assistant can help with</h3><p className="mt-2 text-sm leading-6 text-slate-600">It can identify symptoms mentioned in your description, provide general educational possibilities, highlight urgency, and suggest when to consider professional care.</p><div className="mt-4 space-y-3 border-t border-slate-100 pt-4 text-sm text-slate-600"><p className="flex gap-2"><span className="font-bold text-sky-700">1.</span> Describe your symptoms and how long you’ve had them.</p><p className="flex gap-2"><span className="font-bold text-sky-700">2.</span> Add optional context such as age or existing conditions.</p><p className="flex gap-2"><span className="font-bold text-sky-700">3.</span> Review the guidance and contact a clinician when appropriate.</p></div></article>
        <article className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-950"><h3 className="font-bold">If this feels urgent</h3><p className="mt-1">Do not wait for an online response. Contact your local emergency services or seek urgent medical attention.</p></article>
      </aside>}
    </div>
  </section>;
}

function PatientFeedback() {
  const [category, setCategory] = useState('General feedback');
  const [rating, setRating] = useState(5);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError('');
    setSuccess('');
    setBusy(true);
    try {
      const { data } = await API.post('/feedback/', { category, rating, message });
      setSuccess(data.message);
      setMessage('');
    } catch (e) {
      setError(readError(e));
    } finally {
      setBusy(false);
    }
  }

  return <section className="mx-auto max-w-3xl">
    <SectionHeading title="Share your feedback" description="Help us improve MediAssist AI. Your feedback is saved for the team and emailed when delivery is configured." />
    <Notice error={error} success={success} />
    <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
      <div className="flex items-start gap-3">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sky-50 text-sky-700"><MessageSquare size={21} /></span>
        <div><h2 className="font-bold text-slate-900">How is your experience?</h2><p className="mt-1 text-sm leading-5 text-slate-500">Tell us what works well or what we could make better.</p></div>
      </div>
      <fieldset className="mt-6">
        <legend className="text-sm font-semibold text-slate-800">Your rating</legend>
        <div className="mt-2 flex items-center gap-1" role="radiogroup" aria-label="Rate your experience">
          {[1, 2, 3, 4, 5].map((value) => <button key={value} type="button" role="radio" aria-checked={rating === value} aria-label={`${value} ${value === 1 ? 'star' : 'stars'}`} onClick={() => setRating(value)} className="rounded-lg p-1.5 text-amber-500 transition hover:scale-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-600"><Star size={25} fill={rating >= value ? 'currentColor' : 'none'} /></button>)}
          <span className="ml-2 text-sm text-slate-500">{rating} of 5</span>
        </div>
      </fieldset>
      <label className="mt-5 block text-sm font-semibold text-slate-800">Feedback type<select className={inputClass} value={category} onChange={(event) => setCategory(event.target.value)}><option>General feedback</option><option>Suggestion</option><option>Issue</option></select></label>
      <label className="mt-5 block text-sm font-semibold text-slate-800">Your message<textarea className={inputClass} rows="6" minLength="10" maxLength="3000" required value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Share your thoughts about using MediAssist AI…" /></label>
      <div className="mt-2 flex justify-between gap-3 text-xs text-slate-500"><span>Please don’t include passwords or private medical details.</span><span>{message.length}/3000</span></div>
      <button className={`${buttonClass} mt-5 w-full sm:w-auto`} disabled={busy || message.trim().length < 10}>{busy ? 'Sending feedback…' : <><Send size={16} /> Send feedback</>}</button>
    </form>
  </section>;
}

function TrendCard({ title, description, points, field, color, fill }) {
  const values = points.map((point) => point[field] || 0);
  const previousTotal = values.slice(0, 7).reduce((total, value) => total + value, 0);
  const currentTotal = values.slice(7).reduce((total, value) => total + value, 0);
  const change = previousTotal === 0
    ? currentTotal === 0 ? 0 : 100
    : Math.round(((currentTotal - previousTotal) / previousTotal) * 100);
  const maxValue = Math.max(1, ...values);
  const chartWidth = 560;
  const chartHeight = 150;
  const x = (index) => 10 + index * ((chartWidth - 20) / Math.max(values.length - 1, 1));
  const y = (value) => chartHeight - 12 - (value / maxValue) * (chartHeight - 30);
  const path = values.map((value, index) => `${index === 0 ? 'M' : 'L'} ${x(index)} ${y(value)}`).join(' ');
  const area = `${path} L ${x(values.length - 1)} ${chartHeight - 12} L ${x(0)} ${chartHeight - 12} Z`;
  const TrendIcon = change > 0 ? TrendingUp : change < 0 ? TrendingDown : Minus;
  const trendTone = change > 0 ? 'bg-emerald-50 text-emerald-700' : change < 0 ? 'bg-rose-50 text-rose-700' : 'bg-slate-100 text-slate-600';
  const firstDate = points[0]?.date ? new Date(points[0].date) : null;
  const lastDate = points.at(-1)?.date ? new Date(points.at(-1).date) : null;
  return <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><h3 className="font-bold text-slate-900">{title}</h3><p className="mt-1 text-xs text-slate-500">{description}</p></div>
      <span className={cx('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-bold', trendTone)}><TrendIcon size={14} />{previousTotal === 0 && currentTotal > 0 ? 'New activity' : `${change > 0 ? '+' : ''}${change}% vs previous 7 days`}</span>
    </div>
    <div className="mt-5 flex items-end gap-2"><p className="text-3xl font-bold text-slate-900">{currentTotal}</p><p className="mb-1 text-xs text-slate-500">in the last 7 days</p></div>
    {points.length > 0 && <svg className="mt-4 h-40 w-full overflow-visible" viewBox={`0 0 ${chartWidth} ${chartHeight}`} role="img" aria-label={`${title} over the last 14 days. ${currentTotal} in the latest 7 days, ${previousTotal} in the prior 7 days.`} preserveAspectRatio="none">
      {[0, 1, 2, 3].map((line) => {
        const lineY = 8 + line * ((chartHeight - 20) / 3);
        return <line key={line} x1="8" x2={chartWidth - 8} y1={lineY} y2={lineY} stroke="#e2e8f0" strokeDasharray="4 5" />;
      })}
      <path d={area} fill={fill} opacity="0.45" />
      <path d={path} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      {values.map((value, index) => <circle key={`${points[index]?.date}-${index}`} cx={x(index)} cy={y(value)} r="3" fill="white" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke"><title>{points[index]?.date ? new Date(points[index].date).toLocaleDateString() : ''}: {value}</title></circle>)}
    </svg>}
    <div className="mt-2 flex justify-between text-[11px] text-slate-500"><span>{firstDate?.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span><span>Daily totals · 14 days</span><span>{lastDate?.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span></div>
    <p className="sr-only">Previous seven days: {previousTotal}. Latest seven days: {currentTotal}. Trend: {change > 0 ? 'increasing' : change < 0 ? 'decreasing' : 'unchanged'}.</p>
  </article>;
}

function AdminPanel() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [search, setSearch] = useState('');
  const [departmentName, setDepartmentName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [tab, setTab] = useState('overview');
  async function load() {
    setRefreshing(true);
    try {
      const [s, u, d] = await Promise.all([API.get('/admin/stats'), API.get('/admin/users', { params: search ? { search } : {} }), API.get('/departments/')]);
      setStats(s.data); setUsers(u.data); setDepartments(d.data); setError('');
    } catch (e) { setError(readError(e)); }
    finally { setRefreshing(false); }
  }
  useEffect(() => { load(); }, []);
  useEffect(() => {
    if (tab === 'audit') API.get('/audit/', { params: { limit: 100 } })
      .then(({ data }) => { setAuditLogs(data); setError(''); })
      .catch((e) => setError(readError(e)));
    if (tab === 'feedback') API.get('/feedback/')
      .then(({ data }) => { setFeedback(data); setError(''); })
      .catch((e) => setError(readError(e)));
  }, [tab]);
  async function retryFeedbackEmail(feedbackId) {
    setSuccess('');
    try {
      const { data } = await API.post(`/feedback/${feedbackId}/retry-email`);
      if (data.message) setSuccess(data.message);
      const { data: updatedFeedback } = await API.get('/feedback/');
      setFeedback(updatedFeedback);
    } catch (e) { setError(readError(e)); }
  }
  async function verify(userId, isVerified) {
    try { await API.patch(`/admin/doctors/${userId}/verify`, null, { params: { verify: !isVerified } }); setSuccess(`Doctor credentials ${isVerified ? 'unverified' : 'verified'}.`); await load(); }
    catch (e) { setError(readError(e)); }
  }
  async function toggleActive(user) {
    try { await API.patch(`/admin/users/${user.id}/status`, { is_active: !user.is_active }); setSuccess(`Account ${user.is_active ? 'deactivated' : 'activated'}.`); await load(); }
    catch (e) { setError(readError(e)); }
  }
  async function addDepartment(event) {
    event.preventDefault();
    try { await API.post('/departments/', { name: departmentName }); setDepartmentName(''); setSuccess('Department created.'); await load(); }
    catch (e) { setError(readError(e)); }
  }
  return <section><SectionHeading title="Admin dashboard" description="Manage accounts, doctor verification, departments and platform activity."
    action={<button className={secondaryButtonClass} onClick={load} disabled={refreshing}><Activity size={16} className={refreshing ? 'animate-spin' : ''} />{refreshing ? 'Refreshing…' : 'Refresh dashboard'}</button>} /><Notice error={error} success={success} />
    <div className="mb-6 flex flex-wrap gap-2">{[['overview', 'Overview'], ['users', 'Users & doctors'], ['departments', 'Departments'], ['feedback', 'Patient feedback'], ['audit', 'Audit logs'], ['api-docs', 'API documentation']].map(([id, label]) => <button key={id} onClick={() => setTab(id)} className={cx('rounded-lg px-4 py-2 text-sm font-semibold', tab === id ? 'bg-sky-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200')}>{label}</button>)}</div>
    {tab === 'overview' && stats && <><p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Today · {new Date().toLocaleDateString()}</p><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[['Total users', stats.total_users, Users], ['Patients', stats.total_patients, HeartPulse], ['Doctors', stats.total_doctors, Stethoscope], ['Patients registered today', stats.patient_registrations_today, UserPlus], ['Appointments today', stats.appointments_today, CalendarDays], ['Departments', stats.total_departments, ClipboardList], ['Active accounts', stats.active_users, Check], ['Doctors awaiting verification', stats.unverified_doctors, ShieldCheck]].map(([label, value, Icon]) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"><div className="flex items-center justify-between"><span className="text-sm text-slate-500">{label}</span><Icon className="text-sky-700" size={20} /></div><p className="mt-3 text-3xl font-bold text-slate-900">{value}</p></div>)}</div><div className="mt-6 grid gap-5 xl:grid-cols-2"><TrendCard title="Patient registrations" description="New patient accounts created each day" points={stats.daily_trends || []} field="patient_registrations" color="#0284c7" fill="#7dd3fc" /><TrendCard title="Appointments" description="Appointments scheduled for each day" points={stats.daily_trends || []} field="appointments" color="#7c3aed" fill="#c4b5fd" /></div><div className="mt-6 grid gap-5 lg:grid-cols-2"><article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><div className="mb-5"><h2 className="font-bold text-slate-900">User distribution</h2><p className="mt-1 text-sm text-slate-500">Current account mix across the platform</p></div>{[['Patients', stats.total_patients, 'bg-sky-500'], ['Doctors', stats.total_doctors, 'bg-violet-500'], ['Other accounts', Math.max(0, stats.total_users - stats.total_patients - stats.total_doctors), 'bg-amber-500']].map(([label, value, color]) => <div key={label} className="mb-4 last:mb-0"><div className="mb-2 flex justify-between text-sm"><span className="font-medium text-slate-700">{label}</span><span className="text-slate-500">{value}</span></div><div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className={cx('h-full rounded-full transition-all', color)} style={{ width: `${stats.total_users ? Math.min(100, (value / stats.total_users) * 100) : 0}%` }} /></div></div>)}</article><article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><div className="mb-5"><h2 className="font-bold text-slate-900">Platform health</h2><p className="mt-1 text-sm text-slate-500">Account activity and verification status</p></div><div className="grid grid-cols-2 gap-3"><div className="rounded-xl bg-emerald-50 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Active accounts</p><p className="mt-2 text-2xl font-bold text-emerald-900">{stats.active_users}</p></div><div className="rounded-xl bg-amber-50 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Pending reviews</p><p className="mt-2 text-2xl font-bold text-amber-900">{stats.unverified_doctors}</p></div></div><p className="mt-4 text-sm leading-6 text-slate-500">{stats.unverified_doctors ? 'Review unverified doctor accounts to confirm their professional credentials.' : 'All doctor accounts are verified. Keep monitoring account activity from this dashboard.'}</p></article></div><div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-900"><strong>Credential review:</strong> {stats.unverified_doctors} doctor account(s) are awaiting verification. Review license details in Users & doctors before marking them verified.</div></>}
    {tab === 'users' && <><form onSubmit={(e) => { e.preventDefault(); load(); }} className="mb-4 flex gap-2"><input className={inputClass} placeholder="Search by name or email" value={search} onChange={(e) => setSearch(e.target.value)} /><button className={buttonClass}><Search size={16} /> Search</button></form><div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white"><table className="w-full min-w-[760px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-5 py-4">Name</th><th className="px-5 py-4">Email</th><th className="px-5 py-4">Role</th><th className="px-5 py-4">Status</th><th className="px-5 py-4">Actions</th></tr></thead><tbody className="divide-y divide-slate-100">{users.map((u) => <tr key={u.id}><td className="px-5 py-4 font-medium">{u.full_name}</td><td className="px-5 py-4">{u.email}</td><td className="px-5 py-4 capitalize">{u.role}</td><td className="px-5 py-4"><span className={cx('rounded-full px-2.5 py-1 text-xs font-semibold', u.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600')}>{u.is_active ? 'Active' : 'Inactive'}{u.role === 'doctor' && !u.is_verified ? ' · Unverified' : ''}</span></td><td className="px-5 py-4"><div className="flex gap-2">{u.role === 'doctor' && <button onClick={() => verify(u.id, u.is_verified)} className="rounded-lg bg-sky-50 px-3 py-2 text-xs font-semibold text-sky-700">{u.is_verified ? 'Revoke verification' : 'Verify doctor'}</button>}<button onClick={() => toggleActive(u)} className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">{u.is_active ? 'Deactivate' : 'Activate'}</button></div></td></tr>)}</tbody></table></div></>}
    {tab === 'departments' && <><form onSubmit={addDepartment} className="mb-5 flex gap-2 rounded-2xl border border-slate-200 bg-white p-4"><input className={inputClass} required minLength="2" placeholder="New department name" value={departmentName} onChange={(e) => setDepartmentName(e.target.value)} /><button className={buttonClass}><UserPlus size={16} /> Add department</button></form><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{departments.map((d) => <article key={d.id} className="rounded-xl border border-slate-200 bg-white p-4"><h3 className="font-semibold text-slate-900">{d.name}</h3><p className="mt-1 text-sm text-slate-500">{d.description || 'No description'}</p></article>)}</div></>}
    {tab === 'feedback' && <div className="space-y-4">{feedback.length ? feedback.map((entry) => <article key={entry.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex flex-wrap items-center gap-2"><h3 className="font-bold text-slate-900">{entry.category}</h3><span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">{'★'.repeat(entry.rating)}{'☆'.repeat(5 - entry.rating)} · {entry.rating}/5</span></div><p className="mt-1 text-xs text-slate-500">{entry.patient_name} · {entry.patient_email} · {new Date(entry.created_at).toLocaleString()}</p></div><span className={cx('rounded-full px-2.5 py-1 text-xs font-semibold capitalize', entry.email_status === 'sent' ? 'bg-emerald-50 text-emerald-700' : entry.email_status === 'failed' ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-700')}>Email {entry.email_status}</span></div><p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-slate-700">{entry.message}</p>{entry.email_status !== 'sent' && <button onClick={() => retryFeedbackEmail(entry.id)} className={`${secondaryButtonClass} mt-4`}><Mail size={15} /> Retry email</button>}</article>) : <Empty title="No patient feedback yet" detail="Patient platform reviews will appear here after they are submitted." />}</div>}
    {tab === 'api-docs' && <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-5"><div><h2 className="font-bold text-slate-900">API documentation</h2><p className="mt-1 text-sm text-slate-500">Explore and try the MediAssist AI API endpoints.</p></div><a href={`${API.defaults.baseURL.replace(/\/$/, '')}/docs`} target="_blank" rel="noreferrer" className={secondaryButtonClass}><BookOpen size={16} /> Open in new tab</a></div><iframe title="MediAssist AI API documentation" src={`${API.defaults.baseURL.replace(/\/$/, '')}/docs`} className="h-[75vh] min-h-[600px] w-full border-0" loading="lazy" /></section>}
    {tab === 'audit' && <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white"><table className="w-full min-w-[700px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-5 py-4">Timestamp</th><th className="px-5 py-4">Action</th><th className="px-5 py-4">Resource</th><th className="px-5 py-4">User ID</th><th className="px-5 py-4">IP address</th></tr></thead><tbody className="divide-y divide-slate-100">{auditLogs.map((log) => <tr key={log.id}><td className="px-5 py-4 whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</td><td className="px-5 py-4 font-medium">{log.action}</td><td className="px-5 py-4">{log.resource}{log.resource_id && ` · ${log.resource_id}`}</td><td className="px-5 py-4 font-mono text-xs">{log.user_id || '—'}</td><td className="px-5 py-4">{log.ip_address || '—'}</td></tr>)}</tbody></table>{!auditLogs.length && <p className="p-8 text-center text-sm text-slate-500">No audit events found.</p>}</div>}
  </section>;
}

function DoctorDashboard({ user }) {
  const [data, setData] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function load() {
    try {
      const [dashboard, schedule] = await Promise.all([
        API.get('/doctors/me/dashboard'),
        API.get('/appointments/my'),
      ]);
      setData(dashboard.data);
      setAppointments(schedule.data);
      setError('');
    } catch (e) { setError(readError(e)); }
  }
  useEffect(() => { load(); }, []);
  async function changeAvailability() {
    setBusy(true);
    try { await API.patch('/doctors/me/availability', { available: !data.available }); await load(); }
    catch (e) { setError(readError(e)); } finally { setBusy(false); }
  }
  const pendingCount = appointments.filter((appointment) => appointment.status === 'pending').length;
  const today = dateToday();
  return <section className="space-y-7">
    <div className="overflow-hidden rounded-3xl bg-gradient-to-r from-sky-950 via-sky-900 to-cyan-800 p-7 text-white shadow-sm sm:p-9">
      <p className="text-sm font-semibold text-sky-200">DOCTOR WORKSPACE</p>
      <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Good day, Dr. {user.full_name}</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-sky-100 sm:text-base">Here’s your practice overview. Keep your schedule moving and stay connected with your patients.</p>
      <button onClick={() => window.dispatchEvent(new CustomEvent('app:navigate', { detail: 'appointments' }))} className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-sky-900 shadow-sm hover:bg-sky-50">Open appointments <ChevronRight size={16} /></button>
    </div>
    <Notice error={error} />
    {data && <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ['Today’s appointments', appointments.filter((appointment) => appointment.appointment_date === today).length, CalendarDays, 'bg-sky-50 text-sky-700'],
          ['Needs your attention', pendingCount, Bell, 'bg-amber-50 text-amber-700'],
          ['Availability', data.available ? 'Available' : 'Paused', Check, data.available ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'],
          ['Verification', data.is_verified ? 'Verified' : 'Pending', ShieldCheck, data.is_verified ? 'bg-emerald-50 text-emerald-700' : 'bg-violet-50 text-violet-700'],
        ].map(([label, value, Icon, tone]) => <article key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><span className={cx('flex h-11 w-11 items-center justify-center rounded-xl', tone)}><Icon size={20} /></span><p className="mt-4 text-sm text-slate-500">{label}</p><p className="mt-1 text-2xl font-bold text-slate-900">{value}</p></article>)}
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.3fr_0.7fr]">
        <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="font-bold text-slate-900">Recent appointments</h2><p className="mt-1 text-xs text-slate-500">Your latest patient bookings</p></div><button onClick={() => window.dispatchEvent(new CustomEvent('app:navigate', { detail: 'appointments' }))} className="text-sm font-semibold text-sky-700 hover:text-sky-900">View all</button></div>
          {appointments.length ? <div className="divide-y divide-slate-100">{appointments.slice(0, 5).map((appointment) => <div key={appointment.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"><div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-50 text-sky-700"><Users size={18} /></span><div><p className="text-sm font-semibold text-slate-900">{appointment.patient?.full_name || 'Patient'}</p><p className="mt-1 text-xs text-slate-500">{appointment.appointment_date} · {appointment.start_time?.slice(0, 5)}</p></div></div><Status status={appointment.status} /></div>)}</div> : <div className="px-5 py-12 text-center"><CalendarDays className="mx-auto text-slate-400" /><p className="mt-3 font-semibold text-slate-800">No appointments yet</p><p className="mt-1 text-sm text-slate-500">New patient bookings will appear here.</p></div>}
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-50 text-sky-700"><Stethoscope size={21} /></div>
          <h2 className="mt-4 text-lg font-bold text-slate-900">Practice settings</h2><p className="mt-1 text-sm text-slate-500">{data.specialization || 'Specialization not set'} · Consultation fee {data.consultation_fee}</p>
          <div className="mt-5 flex items-center justify-between rounded-xl bg-slate-50 p-4"><div><p className="text-sm font-semibold text-slate-800">Accept new bookings</p><p className="mt-1 text-xs text-slate-500">{data.available ? 'Patients can book with you' : 'New bookings are paused'}</p></div><button aria-label={data.available ? 'Pause bookings' : 'Accept bookings'} onClick={changeAvailability} disabled={busy} className={cx('relative h-7 w-12 rounded-full transition', data.available ? 'bg-emerald-500' : 'bg-slate-300')}><span className={cx('absolute top-1 h-5 w-5 rounded-full bg-white shadow transition-all', data.available ? 'left-6' : 'left-1')} /></button></div>
          <button className={`${secondaryButtonClass} mt-4 w-full`} onClick={() => window.dispatchEvent(new CustomEvent('app:navigate', { detail: 'profile' }))}><Settings size={16} /> Edit professional profile</button>
        </article>
      </div>
    </>}
  </section>;
}

function PatientDashboard({ user, onOpen }) {
  const [appointments, setAppointments] = useState([]);
  const [records, setRecords] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => {
    Promise.all([API.get('/appointments/my'), API.get('/records/my')])
      .then(([appointmentResponse, recordResponse]) => {
        setAppointments(appointmentResponse.data);
        setRecords(recordResponse.data);
      })
      .catch((e) => setError(readError(e)));
  }, []);
  const upcoming = appointments.filter((appointment) => appointment.appointment_date >= dateToday() && ['pending', 'confirmed'].includes(appointment.status));
  return <section className="space-y-7">
    <div className="overflow-hidden rounded-3xl bg-gradient-to-r from-sky-950 via-sky-900 to-cyan-800 p-7 text-white shadow-sm sm:p-9">
      <p className="text-sm font-semibold text-sky-200">YOUR PATIENT DASHBOARD</p>
      <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Hello, {user.full_name}</h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-sky-100 sm:text-base">Your care, appointments, and health information in one secure place.</p>
      <button onClick={() => onOpen('doctors')} className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-sky-900 shadow-sm hover:bg-sky-50">Find a doctor <ChevronRight size={16} /></button>
    </div>
    <Notice error={error} />
    <div className="grid gap-4 sm:grid-cols-3">
      {[['Upcoming appointments', upcoming.length, CalendarDays, 'appointments', 'bg-sky-50 text-sky-700'], ['Medical records', records.length, ClipboardList, 'records', 'bg-violet-50 text-violet-700'], ['Doctors available', 'Browse', Stethoscope, 'doctors', 'bg-emerald-50 text-emerald-700']].map(([label, value, Icon, page, tone]) => <button key={label} onClick={() => onOpen(page)} className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"><span className={cx('flex h-12 w-12 shrink-0 items-center justify-center rounded-xl', tone)}><Icon size={21} /></span><span><span className="block text-sm text-slate-500">{label}</span><span className="mt-1 block text-2xl font-bold text-slate-900">{value}</span></span><ChevronRight className="ml-auto text-slate-400" size={18} /></button>)}
    </div>
    <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
      <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="font-bold text-slate-900">Upcoming appointments</h2><p className="mt-1 text-xs text-slate-500">Keep track of your care visits</p></div><button onClick={() => onOpen('appointments')} className="text-sm font-semibold text-sky-700 hover:text-sky-900">View all</button></div>
        {upcoming.length ? <div className="divide-y divide-slate-100">{upcoming.slice(0, 4).map((appointment) => <div key={appointment.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"><div><p className="text-sm font-semibold text-slate-900">Dr. {appointment.doctor?.full_name || 'Doctor'}</p><p className="mt-1 text-xs text-slate-500">{appointment.appointment_date} · {appointment.start_time?.slice(0, 5)}</p></div><Status status={appointment.status} /></div>)}</div> : <div className="px-5 py-10 text-center"><CalendarDays className="mx-auto text-slate-400" /><p className="mt-3 font-semibold text-slate-800">No upcoming appointments</p><p className="mt-1 text-sm text-slate-500">Find a doctor to book your first visit.</p></div>}
      </article>
      <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm font-semibold uppercase tracking-wide text-sky-700">Quick actions</p><div className="mt-3 space-y-2">{[['Book an appointment', 'Choose a doctor and time.', CalendarDays, 'doctors'], ['Review medical records', 'View notes and prescriptions.', ClipboardList, 'records'], ['Symptom assistant', 'Get educational guidance.', Activity, 'symptoms']].map(([title, subtitle, Icon, page]) => <button key={title} onClick={() => onOpen(page)} className="flex w-full items-center gap-3 rounded-xl p-3 text-left transition hover:bg-slate-50"><span className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-50 text-sky-700"><Icon size={18} /></span><span><span className="block text-sm font-semibold text-slate-800">{title}</span><span className="mt-0.5 block text-xs text-slate-500">{subtitle}</span></span><ChevronRight size={16} className="ml-auto text-slate-400" /></button>)}</div></article>
    </div>
  </section>;
}

function Empty({ title, detail }) {
  return <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center"><CalendarDays className="mx-auto text-slate-400" /><h2 className="mt-3 font-semibold text-slate-800">{title}</h2><p className="mt-1 text-sm text-slate-500">{detail}</p></div>;
}

const patientNavigation = [
  ['home', 'Dashboard', LayoutDashboard], ['doctors', 'Find doctors', Stethoscope], ['appointments', 'Appointments', CalendarDays],
  ['records', 'Medical records', ClipboardList], ['symptoms', 'Symptom assistant', Activity],
  ['feedback', 'Share feedback', MessageSquare], ['profile', 'My profile', Users],
];
const doctorNavigation = [
  ['home', 'Dashboard', LayoutDashboard], ['appointments', 'Appointments', CalendarDays],
  ['records', 'Medical records', ClipboardList], ['profile', 'My profile', Users], ['doctors', 'Doctor directory', Stethoscope],
];

export default function App() {
  const { user, loading, logout } = useAuth();
  const [section, setSection] = useState('home');
  const [authOpen, setAuthOpen] = useState(false);
  const [resetToken, setResetToken] = useState(() => {
    const resetPrefix = '#reset-password/';
    return window.location.hash.startsWith(resetPrefix)
      ? window.location.hash.slice(resetPrefix.length)
      : '';
  });
  const [menuOpen, setMenuOpen] = useState(false);
  const [bookingDoctor, setBookingDoctor] = useState(null);
  const [toast, setToast] = useState('');
  const isAdmin = user?.role === 'admin';
  const dashboardMode = Boolean(user && !authOpen && !loading && !resetToken);
  const dashboardNavigation = useMemo(() => {
    if (user?.role === 'admin') return [
      ['admin', 'Admin Dashboard', LayoutDashboard],
      ['doctors', 'Doctor directory', Stethoscope],
      ['appointments', 'Appointments', CalendarDays],
      ['records', 'Medical records', ClipboardList],
      ['profile', 'My profile', Users],
    ];
    if (user?.role === 'doctor') return doctorNavigation;
    if (user?.role === 'patient') return patientNavigation;
    return [];
  }, [user?.role]);
  const publicNavigation = [['home', 'Home', LayoutDashboard], ['doctors', 'Find doctors', Stethoscope]];
  const sectionTitle = {
    home: user?.role === 'doctor' ? 'Doctor dashboard' : user?.role === 'admin' ? 'Admin dashboard' : 'Patient dashboard',
    admin: 'Admin dashboard',
    doctors: 'Doctor directory',
    appointments: 'Appointments',
    records: 'Medical records',
    symptoms: 'Symptom assistant',
    feedback: 'Share feedback',
    profile: 'My profile',
  }[section] || 'MediAssist AI';

  useEffect(() => {
    const navigate = (event) => setSection(event.detail);
    window.addEventListener('app:navigate', navigate);
    return () => window.removeEventListener('app:navigate', navigate);
  }, []);
  useEffect(() => {
    if (user) {
      setAuthOpen(false);
      if (user.role === 'admin') setSection('admin');
      else if (section === 'admin') setSection('home');
      if (section === 'symptoms' && user.role !== 'patient') setSection('home');
      setToast(`Signed in as ${user.role}.`);
    }
  }, [user?.id, user?.role]);

  function openSection(id) {
    if (id === 'admin' && user && user.role !== 'admin') {
      setToast('The Admin Dashboard is available to administrator accounts only.');
      return;
    }
    if (id === 'symptoms' && user && user.role !== 'patient') {
      setToast('The symptom assistant is available to patient accounts only.');
      return;
    }
    if (id === 'feedback' && user && user.role !== 'patient') {
      setToast('Platform feedback is available to patient accounts only.');
      return;
    }
    setSection(id); setAuthOpen(false); setMenuOpen(false); setToast('');
    if (['appointments', 'records', 'symptoms', 'feedback', 'profile', 'admin'].includes(id) && !user) setAuthOpen(true);
  }
  function requestBooking(doctor) {
    if (!user) { setAuthOpen(true); setToast('Sign in as a patient to book an appointment.'); return; }
    if (user.role !== 'patient') { setToast('Only patient accounts can book appointments.'); return; }
    setBookingDoctor(doctor);
  }

  let content;
  if (loading && !resetToken) {
    content = <div className="flex min-h-[55vh] items-center justify-center"><div className="text-center"><div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-sky-200 border-t-sky-700" /><p className="mt-3 text-sm text-slate-500">Loading your account…</p></div></div>;
  } else if (resetToken) {
    content = <ResetPasswordScreen token={resetToken} onComplete={() => {
      window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);
      setResetToken('');
      logout();
      setSection('home');
      setAuthOpen(true);
      setToast('Password reset. Sign in with your new password.');
    }} />;
  } else if (authOpen && !user) {
    content = <AuthScreen onBack={() => { setAuthOpen(false); setSection('home'); }} />;
  } else {
    content = <div className="min-h-[65vh]">
      {section === 'home' && (user?.role === 'doctor' ? <DoctorDashboard user={user} /> : user?.role === 'patient' ? <PatientDashboard user={user} onOpen={openSection} /> : isAdmin ? <AdminPanel /> : <Landing onOpen={openSection} />)}
      {section === 'doctors' && <Doctors onBook={requestBooking} canBook={user?.role === 'patient'} />}
      {section === 'profile' && user && <Profile user={user} />}
      {section === 'appointments' && user && <Appointments user={user} />}
      {section === 'records' && user && <Records user={user} />}
      {section === 'symptoms' && user?.role === 'patient' && <Symptoms onOpen={openSection} />}
      {section === 'feedback' && user?.role === 'patient' && <PatientFeedback />}
      {section === 'admin' && isAdmin && <AdminPanel />}
    </div>;
  }

  const renderNavigation = (items) => items.map(([id, label, Icon]) => <button key={id} onClick={() => openSection(id)} className={cx('group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition duration-200 active:scale-[0.98]', section === id ? 'bg-sky-500/15 text-sky-200 ring-1 ring-inset ring-sky-400/20' : 'text-slate-300 hover:translate-x-0.5 hover:bg-white/5 hover:text-white')}><Icon size={18} className={cx('transition-transform duration-200', section === id ? 'text-sky-300' : 'text-slate-400 group-hover:text-slate-200 group-hover:scale-105')} /><span>{label}</span>{section === id && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-sky-300 transition-transform duration-200 group-hover:scale-125" />}</button>);

  return <div className="min-h-screen bg-[#f4f8fc] text-slate-800">
    <DisclaimerBanner />
    {dashboardMode ? <div className="flex min-h-[calc(100vh-40px)]">
      {menuOpen && <button aria-label="Close navigation" onClick={() => setMenuOpen(false)} className="fixed inset-0 z-40 bg-slate-950/50 lg:hidden" />}
      <aside className={cx('fixed inset-y-0 left-0 z-50 flex w-[270px] flex-col bg-[#071d36] px-4 py-5 text-white shadow-2xl transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 lg:shadow-none', menuOpen ? 'translate-x-0' : '-translate-x-full')}>
        <div className="flex items-center justify-between px-2">
          <button onClick={() => openSection(user.role === 'admin' ? 'admin' : 'home')} className="flex items-center gap-3 text-left">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-400 text-[#071d36]"><HeartPulse size={23} /></span>
            <span><span className="block font-bold tracking-tight">MediAssist AI</span><span className="text-[11px] text-slate-400">CARE PORTAL</span></span>
          </button>
          <button aria-label="Close navigation" onClick={() => setMenuOpen(false)} className="rounded-lg p-2 text-slate-400 hover:bg-white/10 lg:hidden"><X size={18} /></button>
        </div>
        <div className="mx-2 mt-8 rounded-2xl border border-white/10 bg-white/[0.04] p-3">
          <button onClick={() => openSection('profile')} className="flex w-full items-center gap-3 rounded-xl text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-300"><UserAvatar user={user} size="h-10 w-10" imageClassName="text-sm ring-1 ring-white/15" /><span className="min-w-0"><span className="block truncate text-sm font-semibold">{user.full_name}</span><span className="mt-0.5 block text-xs capitalize text-slate-400">{user.role} account</span></span></button>
        </div>
        <p className="mb-2 mt-8 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Workspace</p>
        <nav className="space-y-1">{renderNavigation(dashboardNavigation)}</nav>
        <div className="mt-auto">
          <div className="border-t border-white/10 pt-3"><button onClick={() => { logout(); setSection('home'); setMenuOpen(false); setToast('You have signed out.'); }} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-rose-500/10 hover:text-rose-200"><LogOut size={18} /> Sign out</button><p className="mt-3 px-3 text-[10px] leading-4 text-slate-500">MediAssist AI is for educational support and is not a diagnostic system.</p></div>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur sm:px-7">
          <div className="flex h-[76px] items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-3">
              <button aria-label="Open navigation" onClick={() => setMenuOpen(true)} className="rounded-xl border border-slate-200 p-2.5 text-slate-600 hover:bg-slate-50 lg:hidden"><Menu size={19} /></button>
              <div className="min-w-0"><p className="hidden text-xs font-medium text-slate-400 sm:block">{new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</p><h1 className="truncate text-lg font-bold text-slate-900 sm:mt-0.5 sm:text-xl">{sectionTitle}</h1></div>
            </div>
            <div className="flex items-center gap-2 sm:gap-3">
              <span className="hidden rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 sm:inline-flex"><span className="mr-2 mt-1 h-1.5 w-1.5 rounded-full bg-emerald-500" />Secure workspace</span>
              <span className="hidden h-8 w-px bg-slate-200 sm:block" />
              <div className="hidden text-right sm:block"><p className="max-w-[180px] truncate text-sm font-semibold text-slate-800">{user.full_name}</p><p className="text-xs capitalize text-slate-500">{user.role}</p></div>
              <button aria-label="Open profile" onClick={() => openSection('profile')} className="rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-600"><UserAvatar user={user} size="h-10 w-10" /></button>
              <button aria-label="Sign out" title="Sign out" onClick={() => { logout(); setSection('home'); setToast('You have signed out.'); }} className="rounded-xl p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-700 lg:hidden"><LogOut size={18} /></button>
            </div>
          </div>
        </header>
        {toast && <div className="mx-4 mt-4 flex items-center justify-between gap-4 rounded-xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm text-sky-900 sm:mx-7"><span>{toast}</span><button aria-label="Dismiss" onClick={() => setToast('')}><X size={15} /></button></div>}
        <main className="mx-auto w-full max-w-[1500px] flex-1 px-4 py-6 sm:px-7 sm:py-8 lg:px-9"><div key={`${section}-${authOpen ? 'auth' : 'content'}`} className="page-transition">{content}</div></main>
        <footer className="mt-auto border-t border-slate-200 bg-white/70 px-5 py-4 text-center text-[11px] text-slate-500 sm:text-left">MediAssist AI · Educational decision support only · Not a diagnostic system</footer>
      </div>
    </div> : <>
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3 sm:px-6">
          <button onClick={() => openSection('home')} className="flex items-center gap-3 text-left"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-100 text-sky-700"><HeartPulse size={24} /></span><span><span className="block font-bold leading-tight text-slate-900">MediAssist AI</span><span className="hidden text-xs text-slate-500 sm:block">Healthcare assistance platform</span></span></button>
          <nav className="hidden items-center gap-1 lg:flex">{publicNavigation.map(([id, label, Icon]) => <button key={id} onClick={() => openSection(id)} className={cx('inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium', section === id ? 'bg-sky-50 text-sky-800' : 'text-slate-600 hover:bg-slate-50')}><Icon size={16} />{label}</button>)}</nav>
          <div className="flex items-center gap-2">
            {!user && <button className="hidden rounded-lg px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50 sm:inline-flex" onClick={() => openSection('admin')}>Admin access</button>}
            <button className={buttonClass} onClick={() => setAuthOpen(true)}>{authOpen ? 'Sign in' : user ? user.full_name : 'Sign in'}</button>
            <button className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden" aria-label="Toggle menu" onClick={() => setMenuOpen(!menuOpen)}><Menu size={21} /></button>
          </div>
        </div>
        {menuOpen && <nav className="grid gap-1 border-t border-slate-100 p-3 lg:hidden">{publicNavigation.map(([id, label, Icon]) => <button key={id} onClick={() => openSection(id)} className={cx('flex items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium', section === id ? 'bg-sky-50 text-sky-800' : 'text-slate-600')}><Icon size={17} />{label}</button>)}<button onClick={() => openSection('admin')} className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium text-slate-600"><ShieldCheck size={17} />Admin access</button><button onClick={() => { setAuthOpen(true); setMenuOpen(false); }} className="rounded-lg px-3 py-2.5 text-left text-sm font-medium text-sky-700">Sign in / Register</button></nav>}
      </header>
      {toast && <div className="fixed right-4 top-24 z-40 flex max-w-sm items-center gap-3 rounded-xl bg-slate-900 px-4 py-3 text-sm text-white shadow-xl"><span>{toast}</span><button aria-label="Dismiss" onClick={() => setToast('')}><X size={15} /></button></div>}
      <div key={`${section}-${authOpen ? 'auth' : 'content'}`} className="page-transition">{content}</div>
      <footer className="border-t border-slate-200 bg-white"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-6 py-5 text-xs text-slate-500"><span>MediAssist AI · Healthcare assistance platform</span><span>Educational decision support only — not a diagnostic system.</span></div></footer>
    </>}
    {bookingDoctor && <BookingModal doctor={bookingDoctor} onClose={(booked) => { setBookingDoctor(null); if (booked) { setToast('Your appointment request was sent.'); setSection('appointments'); } }} />}
  </div>;
}
