export const demoApplications = [
  { id: 'IC-2026-1042', title: 'Fee Installment Request', type: 'Fee Installment', date: '24 Oct 2026', status: 'In Review', priority: 'Medium', office: 'Finance Office' },
  { id: 'IC-2026-1038', title: 'Medical Leave Request', type: 'Leave Request', date: '21 Oct 2026', status: 'Revision Required', priority: 'High', office: 'Student Affairs' },
  { id: 'IC-2026-1029', title: 'Course Registration', type: 'Course Registration', date: '17 Oct 2026', status: 'Approved', priority: 'Low', office: 'Academic Office' },
]
export const demoOpportunities = [
  { title: 'Merit Scholarship 2026', type: 'Scholarship', deadline: '15 Nov 2026', tag: 'Undergraduate', description: 'Merit-based support for eligible students with strong academic performance.' },
  { title: 'Software Engineering Intern', type: 'Internship', deadline: '08 Nov 2026', tag: 'Technology', description: 'A sample opportunity card. Confirm eligibility and details with the relevant office.' },
  { title: 'Final Year Project Showcase', type: 'FYP', deadline: '20 Nov 2026', tag: 'Final year', description: 'Explore project ideas, milestones and supervisor coordination.' },
]
export const applicationTypes = [
  { name: 'Fee Installment', description: 'Request to pay semester dues in installments', office: 'Finance Office', fields: ['Amount due', 'Requested installments', 'Reason'] },
  { name: 'Medical Leave', description: 'Submit a leave request with supporting information', office: 'Student Affairs', fields: ['Start date', 'End date', 'Reason'] },
  { name: 'Course Registration', description: 'Request course registration or add/drop support', office: 'Academic Office', fields: ['Course code', 'Semester', 'Reason'] },
  { name: 'Scholarship Request', description: 'Ask for scholarship consideration or assistance', office: 'Scholarship Office', fields: ['Scholarship name', 'GPA', 'Reason'] },
]
