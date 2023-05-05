import { BASE_URL } from '@/constants';

export function createJobURL(id: string): string {
  return BASE_URL + '/job/' + id;
}

export function createShareURL(query: string): string {
  return BASE_URL + '/share?q=' + encodeURIComponent(query);
}
