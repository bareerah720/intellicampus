import { Link, useLocation } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'
import { demoApplications, demoOpportunities } from '../data/demoData'
const roleConfig = {
 student: { title:'Your campus, connected.', subtitle:'Everything you need for university life, in one place.', cards:[['My applications','Track requests and approvals','/applications','▤'],['Scholarships','Find funding opportunities','/scholarships','✦'],['Opportunity hub','Explore internships and more','/opportunities','↗'],['FYP management','Manage your project journey','/fyp','⌘']] },
 faculty: { title:'Welcome to your faculty workspace.', subtitle:'Review requests, support students and coordinate academic work.', cards:[['Application reviews','View the review queue','/review-applications','▤'],['FYP supervision','Follow project progress','/fyp','⌘'],['Opportunity hub','Explore current opportunities','/opportunities','↗'],['Notifications','Keep up with updates','/notifications','♧']] },
 staff: { title:'Your office workspace.', subtitle:'Keep requests moving through the right approval steps.', cards:[['Office queue','Review application requests','/review-applications','▤'],['Workflows','View approval stages','/workflows','⇢'],['Notifications','Review recent updates','/notifications','♧']] },
 admin: { title:'System overview.', subtitle:'Monitor portal activity and manage university services.', cards:[['User management','Manage roles and accounts','/users','♙'],['All applications','View request activity','/admin-applications','▤'],['Analytics','Explore portal metrics','/analytics','▥'],['Workflow settings','Review approval workflows','/workflows','⇢']] },
 external_examiner: { title:'Evaluation workspace.', subtitle:'Access the FYP evaluation and review journey.', cards:[['FYP evaluations','View project evaluation stages','/fyp','⌘'],['Notifications','Review important updates','/notifications','♧']] },
}
function DashboardHome({ role }) {
 const { user } = useAuth()
 const location = useLocation()
 const c=roleConfig[role]||roleConfig.student
 const name=user?.first_name||user?.username||'there'
 const applicationPath = role === 'student'
  ? '/applications'
  : ['faculty', 'staff'].includes(role)
    ? '/review-applications'
    : role === 'admin'
      ? '/admin-applications'
      : null
 const applicationId = location.state?.applicationId
  ?? new URLSearchParams(location.search).get('applicationId')
 return <DashboardLayout role={role}><div className="hero-panel"><div className="hero-copy"><span className="hero-label"><span/> YOUR INTELLICAMPUS</span><h1>{c.title}</h1><p>{c.subtitle}</p><div className="hero-actions">{applicationPath && <Link to={applicationPath} state={applicationId ? { applicationId } : undefined} className="primary-button">Go to applications <span>→</span></Link>}<Link to="/opportunities" className="hero-link">Explore opportunities ↗</Link></div></div><div className="hero-art"><div className="art-circle circle-one"/><div className="art-circle circle-two"/><div className="art-card"><div className="art-card-top"><span>Campus pulse</span><span className="art-live">● Live preview</span></div><div className="art-stat">Good things<br/>start here<span>✦</span></div><div className="art-progress"><i/></div><small>Your university workspace</small></div><div className="art-floating">✳</div></div></div>
 <div className="section-title"><div><div className="eyebrow">QUICK ACCESS</div><h2>What would you like to do?</h2></div><span className="demo-label">Frontend preview</span></div><div className="quick-grid">{c.cards.map((x,i)=><Link to={x[2]} className="quick-card" key={x[0]}><div className={`quick-icon quick-${i%4}`}>{x[3]}</div><div><h3>{x[0]}</h3><p>{x[1]}</p></div><span className="quick-arrow">↗</span></Link>)}</div>
 <div className="dashboard-lower"><section className="panel"><div className="panel-header"><div><h2>Recent applications</h2><p>Keep an eye on your latest requests.</p></div><Link className="text-link" to={applicationPath || '/applications'}>View all →</Link></div><div className="mini-application-list">{demoApplications.slice(0,3).map(a=><div className="mini-application" key={a.id}><span className="mini-file">▤</span><div><strong>{a.title}</strong><small>{a.id} · {a.date}</small></div><span className={`status-chip ${a.status.toLowerCase().replaceAll(' ','-')}`}>{a.status}</span></div>)}</div><div className="panel-footnote">Sample data only · real records appear after backend integration.</div></section><section className="panel side-feature"><div className="feature-icon">✦</div><div className="eyebrow">DISCOVER</div><h2>New opportunities await</h2><p>Explore scholarships, internships and academic opportunities in one hub.</p><Link to="/opportunities" className="primary-button">Explore hub ↗</Link><div className="feature-count"><strong>{demoOpportunities.length.toString().padStart(2,'0')}</strong><span>sample listings<br/>in this preview</span></div></section></div>
 </DashboardLayout>
}
export default DashboardHome
