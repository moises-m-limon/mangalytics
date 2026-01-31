import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

const supabase = createClient(supabaseUrl, supabaseKey);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, topic } = body;

    // Validate input
    if (!email || !topic) {
      return NextResponse.json(
        { error: 'email and topic are required' },
        { status: 400 }
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'invalid email format' },
        { status: 400 }
      );
    }

    // Insert subscription into Supabase
    const { data, error } = await supabase
      .from('subscriptions')
      .insert([
        {
          email: email.toLowerCase(),
          topic: topic,
          subscribed_at: new Date().toISOString(),
          active: true,
        },
      ])
      .select();

    if (error) {
      // Check if email already exists
      if (error.code === '23505') {
        // Duplicate key error
        return NextResponse.json(
          { error: 'email already subscribed to this topic' },
          { status: 409 }
        );
      }

      console.error('Supabase error:', error);
      return NextResponse.json(
        { error: 'failed to create subscription' },
        { status: 500 }
      );
    }

    return NextResponse.json(
      {
        success: true,
        message: 'subscription created successfully',
        subscription: data[0],
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Subscription error:', error);
    return NextResponse.json(
      { error: 'internal server error' },
      { status: 500 }
    );
  }
}
