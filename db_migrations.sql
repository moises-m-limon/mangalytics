-- Supabase Table Migrations for Mangalytics
-- Run these SQL commands in the Supabase SQL Editor

-- 1. Create recommendation_requests table
CREATE TABLE IF NOT EXISTS recommendation_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL,
  topic TEXT NOT NULL,
  file_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for recommendation_requests
CREATE INDEX IF NOT EXISTS idx_recommendation_requests_email ON recommendation_requests (email);
CREATE INDEX IF NOT EXISTS idx_recommendation_requests_created_at ON recommendation_requests (created_at);

-- 2. Create recommendation_pairings table
CREATE TABLE IF NOT EXISTS recommendation_pairings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id UUID NOT NULL REFERENCES recommendation_requests(id) ON DELETE CASCADE,
  figure_content TEXT NOT NULL,
  image_path TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for recommendation_pairings
CREATE INDEX IF NOT EXISTS idx_recommendation_pairings_request_id ON recommendation_pairings (request_id);

-- 3. Create the reducto-images storage bucket
-- Note: This needs to be done through the Supabase Dashboard or using the Storage API
-- Dashboard: Storage > Create bucket > Name: "reducto-images"
-- Set it to public if you want public URLs, or private for signed URLs

-- To make the bucket public, you can run:
-- INSERT INTO storage.buckets (id, name, public) VALUES ('reducto-images', 'reducto-images', true);

-- To set up RLS policies for the reducto-images bucket (optional):
-- CREATE POLICY "Public Access" ON storage.objects FOR SELECT USING (bucket_id = 'reducto-images');
-- CREATE POLICY "Authenticated users can upload" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'reducto-images' AND auth.role() = 'authenticated');
