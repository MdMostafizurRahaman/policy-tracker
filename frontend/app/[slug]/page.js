import { notFound } from 'next/navigation'

export default async function SlugPage({ params }) {
  const { slug } = await params
  
  // You can add your logic here to handle different slug routes
  // For now, let's just show a basic page or redirect to not found
  
  if (!slug) {
    notFound()
  }
  
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-sm p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Page: {slug}
          </h1>
          <p className="text-gray-600 mb-6">
            This is a dynamic route for slug: <span className="font-mono bg-gray-100 px-2 py-1 rounded">{slug}</span>
          </p>
          
          <div className="border-t pt-6">
            <p className="text-sm text-gray-500">
              You can customize this page to handle different slug routes in your application.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Generate metadata for this page
export async function generateMetadata({ params }) {
  const { slug } = await params
  
  return {
    title: `${slug} | Policy Tracker`,
    description: `Policy Tracker page for ${slug}`,
  }
}