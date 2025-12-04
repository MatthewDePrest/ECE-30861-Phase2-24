import { Builder, By, until } from 'selenium-webdriver'
import chrome from 'selenium-webdriver/chrome'

const TEST_BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:5173'

async function run(){
  const options = new chrome.Options()
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build()
  try{
    await driver.get(TEST_BASE_URL)
    await driver.wait(until.elementLocated(By.xpath("//h6[contains(.,'Trustworthy Model Registry') or contains(.,'Trustworthy')]")), 5000)
    // Click Artifacts tab (should be first tab)
    const listButton = await driver.wait(until.elementLocated(By.xpath("//button[normalize-space()='List Artifacts']")), 5000)
    await listButton.click()
    // Wait for either artifact list item or 'No artifacts yet'
    await driver.wait(async ()=>{
      const els = await driver.findElements(By.css('[role="listitem"]'))
      return els.length>0 || (await driver.findElements(By.xpath("//*[contains(.,'No artifacts yet')]")).then(e=>e.length>0))
    }, 5000)
    console.log('SMOKE: OK')
    await driver.quit()
    process.exit(0)
  }catch(err){
    console.error('SMOKE: FAIL', err)
    await driver.quit()
    process.exit(1)
  }
}

run()
