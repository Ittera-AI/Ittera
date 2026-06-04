import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET() {
  try {
    const htmlPath = path.join(process.cwd(), 'public', 'pitchdeck', 'index.html');
    const html = fs.readFileSync(htmlPath, 'utf-8');
    
    return new NextResponse(html, {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store, no-cache, must-revalidate',
      },
    });
  } catch (error) {
    return new NextResponse('Pitchdeck not found. Please ensure public/pitchdeck/index.html exists.', { status: 404 });
  }
}
