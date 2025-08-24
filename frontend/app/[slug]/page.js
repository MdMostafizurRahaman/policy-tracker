import { notFound, redirect } from 'next/navigation'

// Generate static params for static export
export async function generateStaticParams() {
  // Return common routes that should be pre-generated
  return [
    { slug: 'worldmap' },
    { slug: 'chatbot' },
    { slug: 'ranking' },
    { slug: 'admin' },
    { slug: 'login' },
    { slug: 'signup' },
    { slug: 'submission' },
    { slug: 'admin-login' },
    { slug: 'forget' },
  ]
}

export default async function SlugPage({ params }) {
  const { slug } = await params
  
  // Skip static files like favicon, images, etc.
  if (slug.includes('.') || slug.startsWith('_next') || slug === 'favicon.ico') {
    notFound()
  }
  
  // Valid routes that should redirect to main page
  const validRoutes = ['worldmap', 'chatbot', 'ranking', 'admin', 'login', 'signup', 'submission', 'admin-login', 'forget']
  
  if (validRoutes.includes(slug)) {
    redirect(`/?view=${slug}`)
  }
  
  // For unknown routes, show 404
  notFound()
}

// Generate metadata for this page
export async function generateMetadata({ params }) {
  const { slug } = await params
  
  return {
    title: `${slug} | Policy Tracker`,
    description: `Policy Tracker page for ${slug}`,
  }
}